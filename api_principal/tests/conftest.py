"""Preparacion de las pruebas: base temporal con el esquema y la API en memoria.

Requiere un servidor PostgreSQL accesible. Variables (con valores por defecto
para un servidor local sin contrasena):
    TEST_PG_HOST, TEST_PG_PORT, TEST_PG_USER, TEST_PG_PASSWORD
Cada ejecucion crea la base iotmangrove_test y la elimina al terminar.
"""

import os
import subprocess
import sys
from pathlib import Path

import psycopg
import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "api_principal"))

HOST = os.getenv("TEST_PG_HOST", "/tmp")
PUERTO = os.getenv("TEST_PG_PORT", "5433")
USUARIO = os.getenv("TEST_PG_USER", "postgres")
CLAVE = os.getenv("TEST_PG_PASSWORD", "")
BASE = "iotmangrove_test"
CLAVE_GATEWAY = "clave-de-prueba-del-gateway-000000"
CLAVE_ADMIN = "AdminDePrueba#2026"


def _conectar(base: str):
    return psycopg.connect(host=HOST, port=PUERTO, user=USUARIO, password=CLAVE or None,
                           dbname=base, autocommit=True)


@pytest.fixture(scope="session")
def cliente():
    with _conectar("postgres") as c:
        c.execute(f"DROP DATABASE IF EXISTS {BASE}")
        c.execute(f"CREATE DATABASE {BASE}")
    with _conectar(BASE) as c:
        for nombre in ("01_esquema.sql", "02_semillas.sql", "03_datos_demo.sql", "04_ambitos_y_riego.sql"):
            c.execute((RAIZ / "db" / "principal" / nombre).read_text(encoding="utf-8"))
    os.environ.update({
        "DB_HOST": HOST, "DB_PORT": PUERTO, "DB_NAME": BASE, "DB_USER": USUARIO,
        "DB_PASSWORD": CLAVE or "sin-clave", "DB_SSLMODE": "disable",
        "JWT_SECRET": "x" * 40, "ADMIN_PASSWORD": CLAVE_ADMIN,
        "GATEWAY_CODE": "0XDD", "GATEWAY_API_KEY": CLAVE_GATEWAY,
    })
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as tc:
        yield tc
    with _conectar("postgres") as c:
        c.execute(f"DROP DATABASE IF EXISTS {BASE} WITH (FORCE)")


@pytest.fixture(scope="session")
def admin(cliente):
    r = cliente.post("/api/auth/login", json={"username": "admin", "password": CLAVE_ADMIN})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def gw():
    return {"X-API-Key": CLAVE_GATEWAY}


@pytest.fixture(scope="session")
def consulta(cliente):
    cliente.post("/api/auth/registro", json={"username": "lector", "password": "lector123"})
    r = cliente.post("/api/auth/login", json={"username": "lector", "password": "lector123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
