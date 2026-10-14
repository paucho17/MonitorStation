"""Prueba de humo de extremo a extremo de la API principal.

Uso:
    python scripts/prueba_api.py http://localhost:5000 ADMIN_PASSWORD GATEWAY_API_KEY

Verifica: registro, login, JWT, permisos por rol, CRUD con eliminacion
logica, ingesta con clave de API, generacion de alertas, dashboard,
historial y cierre de sesion (revocacion del token).
"""

import sys
import uuid

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
CLAVE_ADMIN = sys.argv[2] if len(sys.argv) > 2 else "Admin#Prueba1"
CLAVE_GW = sys.argv[3] if len(sys.argv) > 3 else "clave-gateway-de-prueba-123"

c = httpx.Client(base_url=BASE, timeout=15)
resultados: list[tuple[str, bool, str]] = []


def verificar(nombre: str, condicion: bool, detalle: str = "") -> None:
    resultados.append((nombre, bool(condicion), detalle))
    print(("OK    " if condicion else "FALLO ") + nombre + (f"  [{detalle}]" if not condicion else ""))


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ----------------------------- Autenticacion -----------------------------
r = c.post("/api/auth/login", json={"username": "admin", "password": "incorrecta"})
verificar("login con clave incorrecta devuelve 401", r.status_code == 401, r.text)

r = c.post("/api/auth/login", json={"username": "admin", "password": CLAVE_ADMIN})
verificar("login admin devuelve JWT", r.status_code == 200 and "access_token" in r.json(), r.text)
tok_admin = r.json()["access_token"]
H = auth(tok_admin)

verificar("ruta protegida sin token devuelve 401", c.get("/api/dashboard").status_code == 401)
verificar("token manipulado devuelve 401",
          c.get("/api/dashboard", headers=auth(tok_admin[:-3] + "abc")).status_code == 401)

sufijo = uuid.uuid4().hex[:6]
usuario = f"prueba_{sufijo}"
r = c.post("/api/auth/registro", json={"username": usuario, "password": "Clave123", "email": f"{usuario}@ejemplo.com"})
verificar("registro publico crea usuario", r.status_code == 201, r.text)
r = c.post("/api/auth/registro", json={"username": usuario.upper(), "password": "Clave123"})
verificar("registro duplicado (sin distinguir mayusculas) devuelve 409", r.status_code == 409, r.text)

r = c.post("/api/auth/login", json={"username": usuario, "password": "Clave123"})
tok_consulta = r.json()["access_token"]
HC = auth(tok_consulta)
perfil = c.get("/api/auth/me", headers=HC).json()
verificar("perfil del rol consulta", perfil["rol"] == "consulta" and len(perfil["permisos"]) > 0, str(perfil))

# ----------------------------- Permisos por rol -----------------------------
verificar("consulta puede leer el dashboard", c.get("/api/dashboard", headers=HC).status_code == 200)
verificar("consulta NO puede listar usuarios (403)", c.get("/api/usuarios", headers=HC).status_code == 403)
verificar("consulta NO puede crear zonas (403)",
          c.post("/api/zonas", headers=HC, json={"nombre": "x"}).status_code == 403)

# ----------------------------- CRUD con eliminacion logica -----------------------------
r = c.post("/api/zonas", headers=H, json={"nombre": f"Zona {sufijo}", "municipio": "Prueba", "latitud": 4.5, "longitud": -76.2})
verificar("crear zona", r.status_code == 201 and r.json()["estado"] is True, r.text)
zona = r.json()
verificar("creado y actualizado los asigna la base de datos", zona["creado"] and zona["actualizado"])

r = c.post("/api/zonas", headers=H, json={"nombre": f"Zona {sufijo}"})
verificar("zona duplicada devuelve 409", r.status_code == 409, r.text)
r = c.post("/api/zonas", headers=H, json={"nombre": f"Z {sufijo}", "latitud": 400})
verificar("latitud fuera de rango devuelve 400", r.status_code == 400, r.text)

r = c.put(f"/api/zonas/{zona['id']}", headers=H, json={"descripcion": "editada"})
verificar("actualizar zona", r.status_code == 200 and r.json()["descripcion"] == "editada", r.text)
verificar("el trigger actualiza el campo 'actualizado'", r.json()["actualizado"] > zona["actualizado"],
          f"{zona['actualizado']} -> {r.json()['actualizado']}")

r = c.delete(f"/api/zonas/{zona['id']}", headers=H)
verificar("eliminar zona es logico (estado=false)", r.status_code == 200 and r.json()["estado"] is False, r.text)
lista = c.get("/api/zonas", headers=H).json()["datos"]
verificar("la zona eliminada no aparece en el listado", all(z["id"] != zona["id"] for z in lista))
lista = c.get("/api/zonas?incluir_inactivos=true", headers=H).json()["datos"]
verificar("aparece con incluir_inactivos=true", any(z["id"] == zona["id"] for z in lista))
r = c.post(f"/api/zonas/{zona['id']}/restaurar", headers=H)
verificar("restaurar zona", r.status_code == 200 and r.json()["estado"] is True, r.text)

r = c.post("/api/usuarios", headers=H, json={"rol_id": 2, "username": f"op_{sufijo}", "password": "Operador1"})
verificar("crear usuario operador (sin exponer el hash)",
          r.status_code == 201 and "password_hash" not in r.json() and "password" not in r.json(), r.text)
r = c.post("/api/auth/login", json={"username": f"op_{sufijo}", "password": "Operador1"})
HO = auth(r.json()["access_token"])
verificar("operador puede crear zonas", c.post("/api/zonas", headers=HO, json={"nombre": f"Op {sufijo}"}).status_code == 201)
verificar("operador NO puede ver usuarios (403)", c.get("/api/usuarios", headers=HO).status_code == 403)

r = c.get("/api/auth/me", headers=H).json()
verificar("admin no puede eliminarse a si mismo",
          c.delete(f"/api/usuarios/{r['id']}", headers=H).status_code == 400)

# ----------------------------- Ingesta -----------------------------
trama = {"gateway": "0xDD", "nodeID": "0xAA", "type": "WATER", "rssi": -90, "snr": 7.5,
         "latitude": 4.1234, "longitude": -76.1234, "satellites": 8,
         "data": {"ph": 9.4, "turbidity": 20.5, "mq135_raw": 500, "tds": -5}}
verificar("ingesta sin API key devuelve 401", c.post("/api/ingest", json=trama).status_code == 401)
verificar("ingesta con API key invalida devuelve 401",
          c.post("/api/ingest", json=trama, headers={"X-API-Key": "mala"}).status_code == 401)
r = c.post("/api/ingest", json=trama, headers={"X-API-Key": CLAVE_GW})
verificar("ingesta valida devuelve 201", r.status_code == 201, r.text)
cuerpo = r.json()
verificar("pH 9.4 genera alerta CRITICO", any(a["variable"] == "ph" and a["nivel"] == "CRITICO" for a in cuerpo["alertas"]), str(cuerpo))
verificar("variable retirada (mq135_raw) se ignora", "mq135_raw" in cuerpo["ignoradas"], str(cuerpo))
verificar("valor fuera del rango fisico se descarta", "tds" in cuerpo["descartadas"], str(cuerpo))

r = c.post("/api/ingest", headers={"X-API-Key": CLAVE_GW}, json={
    "nodeID": "0xee", "type": "AMB", "rssi": -80, "snr": 5,
    "data": {"temperature": 30.1, "humidity": 66, "pressure": 1008, "eco2": 650, "tvoc": 40}})
verificar("nodo nuevo se registra automaticamente", r.status_code == 201 and r.json()["mediciones"] == 5, r.text)
r = c.post("/api/ingest", headers={"X-API-Key": CLAVE_GW}, json={"nodeID": "0xff", "type": "NOEXISTE", "data": {}})
verificar("tipo de nodo desconocido devuelve 400", r.status_code == 400, r.text)

# ----------------------------- Lectura de datos -----------------------------
d = c.get("/api/dashboard", headers=HC).json()
codigos = {v["variable"] for v in d["variables"]}
verificar("dashboard incluye variables de varios nodos", {"ph", "temperature", "soil_humidity"} <= codigos, str(codigos))
verificar("dashboard informa la posicion GPS", d["ultima_posicion"] is not None and abs(d["ultima_posicion"]["latitud"] - 4.1234) < 1e-6, str(d["ultima_posicion"]))
verificar("dashboard cuenta alertas pendientes", d["alertas_pendientes"] >= 1)

h = c.get("/api/historial?nodo=0xaa&variable=ph&limite=5", headers=HC).json()
verificar("historial filtra por nodo y variable", h["total"] >= 1 and all(f["variable"] == "ph" for f in h["datos"]), str(h)[:200])

al = c.get("/api/alertas?atendida=false", headers=HO).json()
verificar("operador consulta alertas", al["total"] >= 1)
id_al = al["datos"][0]["id"]
r = c.put(f"/api/alertas/{id_al}", headers=HO, json={"atendida": True})
verificar("operador marca la alerta como atendida", r.status_code == 200 and r.json()["atendida"] is True, r.text)

# ----------------------------- Gateways -----------------------------
r = c.post("/api/gateways", headers=H, json={"codigo": f"gw{sufijo}", "nombre": "Gateway de prueba"})
verificar("crear gateway devuelve la clave una sola vez", r.status_code == 201 and "api_key" in r.json(), r.text)
clave_nueva = r.json()["api_key"]
r = c.post("/api/ingest", headers={"X-API-Key": clave_nueva}, json={"nodeID": "0xCC", "type": "SOIL", "data": {"soilHumidity": 55}})
verificar("el gateway nuevo puede enviar datos", r.status_code == 201, r.text)
gws = c.get("/api/gateways", headers=H).json()["datos"]
verificar("el listado de gateways no expone la clave", all("api_key_hash" not in g for g in gws))

# ----------------------------- Cierre de sesion -----------------------------
verificar("logout devuelve 200", c.post("/api/auth/logout", headers=HC).status_code == 200)
verificar("token revocado devuelve 401", c.get("/api/dashboard", headers=HC).status_code == 401)

fallos = [r for r in resultados if not r[1]]
print(f"\n{len(resultados) - len(fallos)}/{len(resultados)} pruebas correctas")
sys.exit(1 if fallos else 0)
