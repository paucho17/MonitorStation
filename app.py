import os
import socket
import threading
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional, Union

import psycopg
import uvicorn
from fastapi import Depends, FastAPI, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool
from zeroconf import ServiceInfo, Zeroconf

PORT = int(os.getenv("PORT", "5000"))
STATIC_DIR = Path(__file__).parent / "static"


# ----------------------------- PostgreSQL CONNECTION -----------------------------
# Las credenciales vienen de variables de entorno (no van en el código).
_pool: Optional[ConnectionPool] = None


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo="",
            kwargs={
                "host": os.environ["DB_HOST"],
                "port": int(os.getenv("DB_PORT", "5432")),
                "dbname": os.environ["DB_NAME"],
                "user": os.environ["DB_USER"],
                "password": os.environ["DB_PASSWORD"],
                "sslmode": os.getenv("DB_SSLMODE", "prefer"),
                "row_factory": dict_row,  # las filas salen como dict
            },
            min_size=1,
            max_size=int(os.getenv("DB_POOL_SIZE", "5")),
            timeout=float(os.getenv("DB_POOL_TIMEOUT", "10")),
            open=True,
        )
    return _pool


def get_db():
    """Dependencia: entrega una conexión y la devuelve al pool al terminar."""
    with get_pool().connection() as conn:
        yield conn


# ----------------------------- AUTH -----------------------------
SESSION_TOKENS: dict[str, str] = {}


class Unauthorized(Exception):
    pass


def require_token(authorization: Optional[str] = Header(None)) -> str:
    """Dependencia: reemplaza a require_token(request) de Flask."""
    if not authorization or authorization not in SESSION_TOKENS:
        raise Unauthorized()
    return SESSION_TOKENS[authorization]


# ----------------------------- SCHEMAS -----------------------------
class RegisterIn(BaseModel):
    username: str = ""
    password: str = ""
    email: Optional[str] = None


class LoginIn(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None


class LogoutIn(BaseModel):
    token: Optional[str] = None


class IngestIn(BaseModel):
    gateway: str = "unknown"
    nodeID: str = "unknown"
    type: str = "unknown"
    rssi: Union[int, float] = 0
    snr: Union[int, float] = 0.0
    data: dict[str, Any] = {}


# ----------------------------- mDNS / UDP DISCOVERY -----------------------------
def get_local_ip() -> str:
    """Obtiene la IP local de manera confiable"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def register_mdns_service():
    try:
        zeroconf = Zeroconf()
        local_ip = get_local_ip()

        info = ServiceInfo(
            "_http._tcp.local.",
            "flaskserver._http._tcp.local.",
            addresses=[socket.inet_aton(local_ip)],
            port=PORT,
            properties={},
            server="flaskserver.local.",
        )

        zeroconf.register_service(info)
        print(f"[mDNS] Servidor anunciado como flaskserver.local (IP: {local_ip})")
        return zeroconf, info
    except Exception as e:
        print(f"[mDNS] Error al registrar servicio: {e}")
        print("[mDNS] Continuando sin mDNS (UDP discovery aún disponible)")
        return None


def unregister_mdns_service(handle):
    zeroconf, info = handle
    try:
        zeroconf.unregister_service(info)
        zeroconf.close()
    except Exception as e:
        print(f"[mDNS] Error al cerrar servicio: {e}")


def udp_discovery_listener():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", 4210))

        print("[UDP] Discovery escuchando en puerto 4210")

        while True:
            data, addr = sock.recvfrom(1024)
            if data.decode() == "DISCOVER_SERVER":
                print(f"[UDP] Petición de discovery desde {addr[0]}")
                sock.sendto(b"SERVER_HERE", addr)
    except Exception as e:
        print(f"[UDP] Error en discovery listener: {e}")


# ----------------------------- LIFESPAN (startup / shutdown) -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 60)
    print("🚀 INICIANDO SERVIDOR FASTAPI")
    print("=" * 60)

    # zeroconf es bloqueante: se ejecuta fuera del event loop
    mdns_handle = await run_in_threadpool(register_mdns_service)
    threading.Thread(target=udp_discovery_listener, daemon=True).start()

    print("\n📡 Endpoints disponibles:")
    print("   POST /api/register        - Registro de nuevo usuario")
    print("   POST /api/login           - Autenticación de usuario")
    print("   POST /api/logout          - Cerrar sesión")
    print("   POST /api/ingest          - Recibir datos del gateway LoRa")
    print("   GET  /api/latest          - Últimos datos (requiere auth)")
    print("   GET  /api/latest-complete - Últimos datos completos sin nulls (requiere auth)")
    print("   GET  /api/history         - Historial de datos (requiere auth)")
    print("   GET  /                    - Página de login")
    print("   GET  /docs                - Documentación interactiva")
    print("\n" + "=" * 60 + "\n")

    yield

    if mdns_handle:
        await run_in_threadpool(unregister_mdns_service, mdns_handle)
    if _pool is not None:
        await run_in_threadpool(_pool.close)


app = FastAPI(title="Sistema de Monitoreo", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ----------------------------- ERROR HANDLERS -----------------------------
@app.exception_handler(Unauthorized)
async def unauthorized_handler(request: Request, exc: Unauthorized):
    return JSONResponse({"error": "Unauthorized"}, status_code=401)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    # Flask devolvía 400; FastAPI por defecto devuelve 422. Se mantiene el 400.
    return JSONResponse(
        {"success": False, "message": "Datos inválidos", "error": "No valid JSON data received"},
        status_code=400,
    )


# ----------------------------- REGISTER -----------------------------
@app.post("/api/register", status_code=201)
def register(body: RegisterIn, db=Depends(get_db)):
    cursor = None
    try:
        username = body.username.strip()
        password = body.password

        if not username or not password:
            return JSONResponse({"success": False, "message": "Usuario y contraseña son requeridos"}, 400)
        if len(username) < 3:
            return JSONResponse({"success": False, "message": "El usuario debe tener al menos 3 caracteres"}, 400)
        if len(password) < 6:
            return JSONResponse({"success": False, "message": "La contraseña debe tener al menos 6 caracteres"}, 400)

        if len(username) > 50:
            return JSONResponse({"success": False, "message": "El usuario no puede tener más de 50 caracteres"}, 400)

        email = (body.email or "").strip() or None
        if email and len(email) > 100:
            return JSONResponse({"success": False, "message": "El correo no puede tener más de 100 caracteres"}, 400)

        cursor = db.cursor()

        # MySQL comparaba sin distinguir mayúsculas; en PostgreSQL se hace con lower()
        cursor.execute("SELECT id FROM users WHERE lower(username)=lower(%s)", (username,))
        if cursor.fetchone():
            return JSONResponse({"success": False, "message": "El usuario ya existe"}, 409)

        cursor.execute(
            "INSERT INTO users (username, email, passkey) VALUES (%s, %s, %s) RETURNING id",
            (username, email, password),
        )
        user_id = cursor.fetchone()["id"]
        db.commit()

        print(f"✅ Usuario registrado: {username} (ID: {user_id})")

        return {"success": True, "message": "Usuario registrado exitosamente", "user_id": user_id}

    except psycopg.errors.UniqueViolation:
        # dos registros simultáneos, o correo repetido
        db.rollback()
        return JSONResponse({"success": False, "message": "El usuario o el correo ya existe"}, 409)

    except psycopg.Error as db_err:
        print(f"❌ Error de base de datos en registro: {db_err}")
        db.rollback()
        return JSONResponse({"success": False, "message": "Error en la base de datos"}, 500)

    except Exception as e:
        print(f"❌ Error en registro: {e}")
        db.rollback()
        return JSONResponse({"success": False, "message": "Error del servidor"}, 500)

    finally:
        if cursor:
            cursor.close()


# ----------------------------- LOGIN -----------------------------
@app.post("/api/login")
def login(body: LoginIn, db=Depends(get_db)):
    cursor = None
    try:
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE lower(username)=lower(%s) AND passkey=%s",
            (body.username, body.password),
        )
        user = cursor.fetchone()

        if user:
            token = str(uuid.uuid4())
            SESSION_TOKENS[token] = body.username
            print(f"✅ Login exitoso: {body.username}")
            return {"success": True, "token": token, "username": body.username}

        return JSONResponse({"success": False, "message": "Credenciales inválidas"}, 401)

    except Exception as e:
        print(f"❌ Error en login: {e}")
        return JSONResponse({"success": False, "message": "Error del servidor"}, 500)

    finally:
        if cursor:
            cursor.close()


# ----------------------------- LOGOUT -----------------------------
@app.post("/api/logout")
def logout(body: LogoutIn):
    if body.token in SESSION_TOKENS:
        username = SESSION_TOKENS.pop(body.token)
        print(f"✅ Logout: {username}")
    return {"success": True}


# ----------------------------- INGEST DATA -----------------------------
@app.post("/api/ingest")
def ingest(payload: IngestIn, db=Depends(get_db)):
    """Recibe datos del gateway LoRa y los guarda en la base de datos"""
    cursor = None
    try:
        if not payload.model_fields_set:  # {} vacío: Flask lo rechazaba con 400
            return JSONResponse({"error": "No JSON data received"}, 400)

        data = payload.data
        sensor_type = payload.type

        print("\n" + "=" * 60)
        print("📥 DATOS RECIBIDOS DEL GATEWAY")
        print("=" * 60)
        print(f"Gateway: {payload.gateway}")
        print(f"Nodo:    {payload.nodeID}")
        print(f"Tipo:    {sensor_type}")
        print(f"RSSI:    {payload.rssi} dBm")
        print(f"SNR:     {payload.snr} dB")
        print(f"Data:    {data}")
        print("=" * 60 + "\n")

        ph = turbidity = humidity = temperature = None
        mq135_raw = resistance = ppm = correctedppm = soil_humidity = None

        if sensor_type == "WATER":
            ph = float(data.get("ph", 0))
            turbidity = float(data.get("turbidity", 0))

        elif sensor_type == "AMB":
            humidity = float(data.get("humidity", 0))
            temperature = float(data.get("temperature", 0))
            mq135_raw = int(data.get("mq135_raw", 0)) if data.get("mq135_raw") else None
            resistance = float(data.get("resistance", 0)) if data.get("resistance") else None
            ppm = float(data.get("ppm", 0)) if data.get("ppm") else None
            correctedppm = float(data.get("correctedppm", 0)) if data.get("correctedppm") else None

        elif sensor_type == "SOIL":
            soil_humidity = int(data.get("soilHumidity", 0))

        cursor = db.cursor()
        query = """
            INSERT INTO sensor_data
            (gateway, node_id, sensor_type, rssi, snr,
             ph, turbidity, humidity, temperature,
             mq135_raw, resistance, ppm, correctedppm, soil_humidity,
             received_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING id
        """
        values = (
            payload.gateway, payload.nodeID, sensor_type, payload.rssi, payload.snr,
            ph, turbidity, humidity, temperature,
            mq135_raw, resistance, ppm, correctedppm, soil_humidity,
        )
        cursor.execute(query, values)
        inserted_id = cursor.fetchone()["id"]
        db.commit()
        print(f"✅ Datos guardados en BD (ID: {inserted_id})")

        return {
            "success": True,
            "message": "Data saved successfully",
            "id": inserted_id,
            "gateway": payload.gateway,
            "nodeID": payload.nodeID,
            "type": sensor_type,
        }

    except psycopg.Error as db_err:
        print(f"❌ Error de base de datos: {db_err}")
        db.rollback()
        return JSONResponse({"error": "Database error", "details": str(db_err)}, 500)

    except Exception as e:
        print(f"❌ Error procesando datos: {e}")
        db.rollback()
        return JSONResponse({"error": "Internal server error", "details": str(e)}, 500)

    finally:
        if cursor:
            cursor.close()


# ----------------------------- LATEST DATA -----------------------------
@app.get("/api/latest")
def latest(username: str = Depends(require_token), db=Depends(get_db)):
    cursor = None
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM sensor_data ORDER BY received_at DESC LIMIT 1")
        row = cursor.fetchone()
        return row if row else {}

    except Exception as e:
        print(f"❌ Error en latest: {e}")
        return JSONResponse({"error": str(e)}, 500)

    finally:
        if cursor:
            cursor.close()


# ----------------------------- LATEST COMPLETE DATA -----------------------------
@app.get("/api/latest-complete")
def latest_complete(username: str = Depends(require_token), db=Depends(get_db)):
    """
    Obtiene los datos más recientes de cada variable.
    Si una variable es NULL, busca en registros anteriores hasta encontrar un valor.
    """
    cursor = None
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM sensor_data ORDER BY received_at DESC LIMIT 50")
        rows = cursor.fetchall()

        if not rows:
            return {}

        variables = [
            "ph", "turbidity", "humidity", "temperature", "mq135_raw",
            "resistance", "ppm", "correctedppm", "soil_humidity",
        ]

        result = dict(rows[0])

        for var in variables:
            if result.get(var) is None:
                for row in rows:
                    if row.get(var) is not None:
                        result[var] = row[var]
                        print(f"📊 {var}: usando valor de registro anterior ({row['received_at']})")
                        break

        return result

    except Exception as e:
        print(f"❌ Error en latest-complete: {e}")
        return JSONResponse({"error": str(e)}, 500)

    finally:
        if cursor:
            cursor.close()


# ----------------------------- HISTORY -----------------------------
@app.get("/api/history")
def history(username: str = Depends(require_token), db=Depends(get_db)):
    cursor = None
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM sensor_data ORDER BY received_at DESC LIMIT 200")
        return cursor.fetchall()

    except Exception as e:
        print(f"❌ Error en history: {e}")
        return JSONResponse({"error": str(e)}, 500)

    finally:
        if cursor:
            cursor.close()


# ----------------------------- STATIC FILES -----------------------------
# "/" sirve login.html (como en Flask); el resto de archivos sale de /static.
# El mount va AL FINAL para que no tape las rutas /api/*.
@app.get("/", include_in_schema=False)
def root():
    return FileResponse(STATIC_DIR / "login.html")


app.mount("/", StaticFiles(directory=STATIC_DIR), name="static")


# ----------------------------- START -----------------------------
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=True)