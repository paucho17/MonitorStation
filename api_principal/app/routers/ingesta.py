"""Ingesta de tramas LoRa enviadas por el gateway.

El gateway se autentica con la cabecera X-API-Key. Cada trama se guarda
como una lectura (metadatos del radio y GPS) mas una medicion por cada
variable valida. Despues se comparan los valores con los umbrales y se
generan las alertas correspondientes.

Formato esperado (compatible con el firmware existente):

    {
      "gateway": "0xDD",
      "nodeID": "0xAA",
      "type": "WATER",
      "rssi": -95, "snr": 7.5,
      "latitude": 4.1234, "longitude": -76.1234, "satellites": 8,   (opcional)
      "data": {"ph": 7.2, "turbidity": 20.5}
    }
"""

import logging
from typing import Any, Optional

import psycopg
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app.db import get_db, traducir_error
from app.security import hash_clave_api

log = logging.getLogger("iotmangrove.ingesta")
router = APIRouter(prefix="/api", tags=["ingesta"])

# Nombre en la trama -> codigo de la tabla variable. Las claves no
# reconocidas (por ejemplo las del MQ-135 retirado) se ignoran.
ALIAS_VARIABLES = {
    "ph": "ph",
    "turbidity": "turbidity",
    "tds": "tds",
    "waterLevel": "water_level",
    "water_level": "water_level",
    "temperature": "temperature",
    "humidity": "humidity",
    "pressure": "pressure",
    "eco2": "eco2",
    "eCO2": "eco2",
    "tvoc": "tvoc",
    "TVOC": "tvoc",
    "soilHumidity": "soil_humidity",
    "soil_humidity": "soil_humidity",
}


class IngestaIn(BaseModel):
    gateway: Optional[str] = Field(default=None, max_length=20)
    nodeID: str = Field(min_length=1, max_length=20)
    type: str = Field(min_length=1, max_length=20)
    rssi: Optional[float] = None
    snr: Optional[float] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    satellites: Optional[int] = Field(default=None, ge=0, le=64)
    data: dict[str, Any] = Field(default_factory=dict)


def _numero(valor: Any) -> Optional[float]:
    """Convierte el valor de la trama a numero; None si no es valido."""
    if isinstance(valor, bool):
        return 1.0 if valor else 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    if isinstance(valor, str):
        try:
            return float(valor.replace(",", "."))
        except ValueError:
            return None
    return None


def _fuera_de_rango(valor: float, minimo: Optional[float], maximo: Optional[float]) -> bool:
    return (minimo is not None and valor < minimo) or (maximo is not None and valor > maximo)


@router.post("/ingest", status_code=201, summary="Recibir una trama del gateway (X-API-Key)")
def ingesta(
    trama: IngestaIn,
    x_api_key: Optional[str] = Header(default=None),
    db: psycopg.Connection = Depends(get_db),
):
    if not x_api_key:
        raise HTTPException(401, "Cabecera X-API-Key requerida")

    gateway = db.execute(
        "SELECT id, codigo, zona_id FROM gateway WHERE api_key_hash = %s AND estado = TRUE",
        (hash_clave_api(x_api_key),),
    ).fetchone()
    if gateway is None:
        raise HTTPException(401, "Clave de API inválida")

    codigo_nodo = trama.nodeID.strip().upper()
    tipo = trama.type.strip().upper()
    ignoradas: list[str] = []
    descartadas: list[str] = []

    try:
        nodo = db.execute("SELECT id, estado FROM nodo WHERE codigo = %s", (codigo_nodo,)).fetchone()
        if nodo is None:
            tipo_nodo = db.execute(
                "SELECT id FROM tipo_nodo WHERE codigo = %s AND estado = TRUE", (tipo,)
            ).fetchone()
            if tipo_nodo is None:
                raise HTTPException(400, f"Tipo de nodo desconocido: {tipo}")
            # Alta automatica del nodo en el primer mensaje recibido
            nodo = db.execute(
                """INSERT INTO nodo (codigo, nombre, tipo_nodo_id, zona_id, gateway_id)
                   VALUES (%s, %s, %s, %s, %s) RETURNING id, estado""",
                (codigo_nodo, f"Nodo {codigo_nodo}", tipo_nodo["id"], gateway["zona_id"], gateway["id"]),
            ).fetchone()
            log.info("Nodo nuevo registrado automaticamente: %s (%s)", codigo_nodo, tipo)
        elif not nodo["estado"]:
            raise HTTPException(403, "El nodo esta desactivado")

        # Variables y umbrales vigentes
        variables = {
            f["codigo"]: f
            for f in db.execute(
                "SELECT id, codigo, rango_min, rango_max FROM variable WHERE estado = TRUE"
            ).fetchall()
        }

        valores: dict[str, float] = {}
        for clave, bruto in trama.data.items():
            codigo = ALIAS_VARIABLES.get(clave)
            if codigo is None or codigo not in variables:
                ignoradas.append(clave)
                continue
            numero = _numero(bruto)
            var = variables[codigo]
            if numero is None or _fuera_de_rango(numero, var["rango_min"], var["rango_max"]):
                descartadas.append(clave)
                continue
            valores[codigo] = numero

        # El GPS puede venir en la raiz de la trama o dentro de "data"
        latitud = trama.latitude if trama.latitude is not None else _numero(trama.data.get("latitude"))
        longitud = trama.longitude if trama.longitude is not None else _numero(trama.data.get("longitude"))
        satelites = trama.satellites if trama.satellites is not None else _numero(trama.data.get("satellites"))

        lectura = db.execute(
            """INSERT INTO lectura (nodo_id, gateway_id, rssi, snr, latitud, longitud, satelites)
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (nodo["id"], gateway["id"],
             int(trama.rssi) if trama.rssi is not None else None, trama.snr,
             latitud, longitud, int(satelites) if satelites is not None else None),
        ).fetchone()

        alertas: list[dict] = []
        for codigo, valor in valores.items():
            medicion = db.execute(
                "INSERT INTO medicion (lectura_id, variable_id, valor) VALUES (%s, %s, %s) RETURNING id",
                (lectura["id"], variables[codigo]["id"], valor),
            ).fetchone()

            # Se evalua CRITICO primero: solo se genera la alerta mas grave
            umbrales = db.execute(
                """SELECT id, nivel, minimo, maximo, mensaje FROM umbral
                   WHERE variable_id = %s AND estado = TRUE
                   ORDER BY CASE nivel WHEN 'CRITICO' THEN 0 ELSE 1 END""",
                (variables[codigo]["id"],),
            ).fetchall()
            for u in umbrales:
                if _fuera_de_rango(valor, u["minimo"], u["maximo"]):
                    texto = f"{codigo}={valor}: {u['mensaje'] or 'fuera de umbral'}"
                    db.execute(
                        "INSERT INTO alerta (medicion_id, umbral_id, mensaje) VALUES (%s, %s, %s)",
                        (medicion["id"], u["id"], texto),
                    )
                    alertas.append({"variable": codigo, "nivel": u["nivel"], "valor": valor})
                    break

        db.execute("UPDATE gateway SET ultima_conexion = now() WHERE id = %s", (gateway["id"],))
        db.commit()
    except psycopg.Error as exc:
        db.rollback()
        raise traducir_error(exc)

    return {
        "success": True,
        "lectura_id": lectura["id"],
        "nodo": codigo_nodo,
        "mediciones": len(valores),
        "alertas": alertas,
        "ignoradas": ignoradas,
        "descartadas": descartadas,
    }
