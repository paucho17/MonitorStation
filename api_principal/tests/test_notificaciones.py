"""Pruebas de las notificaciones de alertas por correo y del rol "vivero"."""

import os
import socket

import pytest
from aiosmtpd.controller import Controller

from app import notificaciones


class Buzon:
    """Servidor SMTP de prueba que guarda los mensajes recibidos."""

    def __init__(self):
        self.mensajes = []

    async def handle_DATA(self, server, session, envelope):
        self.mensajes.append({"para": envelope.rcpt_tos, "texto": envelope.content.decode("utf-8", "replace")})
        return "250 OK"


@pytest.fixture(scope="module")
def buzon():
    b = Buzon()
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        puerto = s.getsockname()[1]
    ctl = Controller(b, hostname="127.0.0.1", port=puerto)
    ctl.start()
    os.environ.update({"SMTP_HOST": "127.0.0.1", "SMTP_PORT": str(puerto),
                       "SMTP_SECURITY": "none", "SMTP_FROM": "alertas@prueba.test", "ALERT_COOLDOWN_MIN": "60"})
    notificaciones.reiniciar_canales()
    yield b
    ctl.stop()
    notificaciones.reiniciar_canales()


def _usuario(cliente, admin, username, rol, email, **extra):
    rol_id = [r["id"] for r in cliente.get("/api/roles", headers=admin).json()["datos"] if r["nombre"] == rol][0]
    r = cliente.post("/api/usuarios", headers=admin, json={
        "rol_id": rol_id, "username": username, "email": email, "password": "Clave1234", **extra})
    assert r.status_code == 201, r.text
    login = cliente.post("/api/auth/login", json={"username": username, "password": "Clave1234"})
    return r.json()["id"], {"Authorization": f"Bearer {login.json()['access_token']}"}


def _ingesta(cliente, gw, nodo, ph):
    r = cliente.post("/api/ingest", headers=gw, json={"nodeID": nodo, "type": "WATER", "data": {"ph": ph}})
    assert r.status_code == 201, r.text
    return r.json()


def _bitacora(cliente, admin):
    return cliente.get("/api/notificaciones?limite=200", headers=admin).json()["datos"]


def test_aviso_critico_se_envia_una_vez_y_antirrebote(cliente, admin, gw, buzon):
    uid, _ = _usuario(cliente, admin, "avisado", "operador", "avisado@prueba.test",
                      notificar_alertas=True, notificar_nivel="CRITICO")
    r = _ingesta(cliente, gw, "0xN1", 5.0)          # pH 5.0: CRITICO
    assert r["alertas"][0]["nivel"] == "CRITICO"
    assert len(buzon.mensajes) == 1
    assert "avisado@prueba.test" in buzon.mensajes[0]["para"]
    assert "0XN1" in buzon.mensajes[0]["texto"] and "CRITICO" in buzon.mensajes[0]["texto"]
    _ingesta(cliente, gw, "0xN1", 4.9)              # mismo nodo, variable y nivel: antirrebote
    assert len(buzon.mensajes) == 1
    estados = [n["situacion"] for n in _bitacora(cliente, admin) if n["usuario_id"] == uid]
    assert sorted(estados) == ["ENVIADA", "OMITIDA"]


def test_nodo_distinto_si_notifica(cliente, admin, gw, buzon):
    antes = len(buzon.mensajes)
    _ingesta(cliente, gw, "0xN2", 5.0)
    assert len(buzon.mensajes) == antes + 1


def test_nivel_minimo_critico_ignora_advertencias(cliente, admin, gw, buzon):
    antes = len(buzon.mensajes)
    r = _ingesta(cliente, gw, "0xN3", 8.8)          # pH 8.8: solo ADVERTENCIA
    assert r["alertas"][0]["nivel"] == "ADVERTENCIA"
    assert len(buzon.mensajes) == antes


def test_usuario_con_nivel_advertencia_recibe_ambas(cliente, admin, gw, buzon):
    _usuario(cliente, admin, "cauteloso", "consulta", "cauteloso@prueba.test",
             notificar_alertas=True, notificar_nivel="ADVERTENCIA")
    antes = len(buzon.mensajes)
    _ingesta(cliente, gw, "0xN4", 8.8)
    nuevos = buzon.mensajes[antes:]
    assert [m["para"] for m in nuevos] == [["cauteloso@prueba.test"]]


def test_fallo_de_smtp_no_afecta_la_ingesta(cliente, admin, gw, buzon):
    puerto = os.environ["SMTP_PORT"]
    os.environ["SMTP_PORT"] = "1"                    # nadie escucha
    notificaciones.reiniciar_canales()
    try:
        r = _ingesta(cliente, gw, "0xN5", 5.0)
        assert r["success"]
        fallidas = [n for n in _bitacora(cliente, admin) if n["situacion"] == "FALLIDA"]
        assert fallidas and fallidas[0]["detalle"]
    finally:
        os.environ["SMTP_PORT"] = puerto
        notificaciones.reiniciar_canales()


def test_sin_smtp_se_omite(cliente, admin, gw, buzon):
    host = os.environ["SMTP_HOST"]
    os.environ["SMTP_HOST"] = ""
    notificaciones.reiniciar_canales()
    try:
        _ingesta(cliente, gw, "0xN6", 5.0)
        assert any(n["detalle"] == "SMTP no configurado" for n in _bitacora(cliente, admin))
    finally:
        os.environ["SMTP_HOST"] = host
        notificaciones.reiniciar_canales()


def test_preferencias_propias(cliente, admin):
    _, h = _usuario(cliente, admin, "prefe", "consulta", "prefe@prueba.test")
    assert cliente.get("/api/notificaciones/preferencias", headers=h).json()["notificar_alertas"] is False
    r = cliente.put("/api/notificaciones/preferencias", headers=h,
                    json={"notificar_alertas": True, "notificar_nivel": "ADVERTENCIA"})
    assert r.status_code == 200
    assert cliente.get("/api/notificaciones/preferencias", headers=h).json()["notificar_nivel"] == "ADVERTENCIA"
    assert cliente.put("/api/notificaciones/preferencias", headers=h,
                       json={"notificar_alertas": True, "notificar_nivel": "OTRO"}).status_code == 422


def test_sin_correo_no_puede_activar_avisos(cliente, admin):
    rol_id = [r["id"] for r in cliente.get("/api/roles", headers=admin).json()["datos"] if r["nombre"] == "consulta"][0]
    cliente.post("/api/usuarios", headers=admin, json={"rol_id": rol_id, "username": "sincorreo", "password": "Clave1234"})
    h = {"Authorization": "Bearer " + cliente.post("/api/auth/login", json={"username": "sincorreo", "password": "Clave1234"}).json()["access_token"]}
    assert cliente.put("/api/notificaciones/preferencias", headers=h,
                       json={"notificar_alertas": True, "notificar_nivel": "CRITICO"}).status_code == 400


def test_correo_de_prueba(cliente, admin, buzon):
    antes = len(buzon.mensajes)
    assert cliente.post("/api/notificaciones/prueba", headers=admin).status_code in (200, 400)  # admin sin correo -> 400
    _, h = _usuario(cliente, admin, "probador", "operador", "probador@prueba.test")
    assert cliente.post("/api/notificaciones/prueba", headers=h).status_code == 200
    assert len(buzon.mensajes) == antes + 1


# ------------------------------- rol vivero -------------------------------

def test_rol_vivero_permisos(cliente, admin):
    _, h = _usuario(cliente, admin, "vivero1", "vivero", "vivero1@prueba.test")
    perfil = cliente.get("/api/auth/me", headers=h).json()
    modulos = {p["modulo"]: p for p in perfil["permisos"]}
    assert modulos["riego"]["puede_editar"] and modulos["alertas"]["puede_editar"]
    assert not modulos["alertas"]["puede_eliminar"] and "usuarios" not in modulos
    assert cliente.get("/api/riego/estado", headers=h).status_code == 200
    assert cliente.get("/api/dashboard", headers=h).status_code == 200
    assert cliente.get("/api/usuarios", headers=h).status_code == 403
    assert cliente.delete("/api/nodos/1", headers=h).status_code == 403
    alerta = cliente.get("/api/alertas?limite=1", headers=h).json()["datos"][0]
    assert cliente.put(f"/api/alertas/{alerta['id']}", headers=h, json={"atendida": True}).status_code == 200
