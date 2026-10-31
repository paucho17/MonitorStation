"""Notificaciones de alertas por canal (correo electronico).

Cuando la ingesta genera alertas, se avisa a los usuarios que lo pidieron
(usuario.notificar_alertas) y cuyo nivel minimo (usuario.notificar_nivel)
cubre la alerta. Reglas:

  * Una sola vez por alerta y usuario (restriccion UNIQUE en notificacion).
  * Antirrebote: no se repite el aviso del mismo nodo, variable y nivel al
    mismo usuario dentro de ALERT_COOLDOWN_MIN minutos.
  * Un correo por usuario y por trama, con todas sus alertas.
  * Todo intento queda registrado en la tabla notificacion (ENVIADA,
    FALLIDA u OMITIDA), de modo que un fallo del correo nunca afecta la
    ingesta de datos.

Los canales se registran en CANALES. Agregar WhatsApp o SMS consiste en
escribir una clase con el metodo enviar() y anadirla al diccionario.
"""

import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Protocol

import psycopg

from app.db import obtener_pool

log = logging.getLogger("iotmangrove.notificaciones")

NIVELES = {"ADVERTENCIA": 1, "CRITICO": 2}


class Canal(Protocol):
    """Interfaz de un canal de notificacion."""

    nombre: str

    def configurado(self) -> bool: ...

    def enviar(self, destino: str, asunto: str, cuerpo: str) -> None: ...


class CanalCorreo:
    """Envio por SMTP. Funciona con un servidor propio o con un servicio
    transaccional (Brevo, Resend, SES, Mailgun) usando sus credenciales SMTP."""

    nombre = "EMAIL"

    def __init__(self) -> None:
        self.host = os.getenv("SMTP_HOST", "")
        self.puerto = int(os.getenv("SMTP_PORT", "587"))
        self.usuario = os.getenv("SMTP_USER", "")
        self.clave = os.getenv("SMTP_PASSWORD", "")
        self.remitente = os.getenv("SMTP_FROM", "alertas@iotmangrove.info")
        self.seguridad = os.getenv("SMTP_SECURITY", "starttls").lower()  # starttls | ssl | none

    def configurado(self) -> bool:
        return bool(self.host)

    def enviar(self, destino: str, asunto: str, cuerpo: str) -> None:
        msg = EmailMessage()
        msg["From"] = self.remitente
        msg["To"] = destino
        msg["Subject"] = asunto
        msg.set_content(cuerpo)
        contexto = ssl.create_default_context()
        if self.seguridad == "ssl":
            servidor = smtplib.SMTP_SSL(self.host, self.puerto, timeout=15, context=contexto)
        else:
            servidor = smtplib.SMTP(self.host, self.puerto, timeout=15)
        with servidor:
            if self.seguridad == "starttls":
                servidor.starttls(context=contexto)
            if self.usuario:
                servidor.login(self.usuario, self.clave)
            servidor.send_message(msg)


CANALES: dict[str, Canal] = {}


def _canales() -> dict[str, Canal]:
    """Crea los canales una vez, leyendo el entorno al primer uso."""
    if not CANALES:
        correo = CanalCorreo()
        CANALES[correo.nombre] = correo
    return CANALES


def reiniciar_canales() -> None:
    """Fuerza a releer la configuracion (usado en las pruebas)."""
    CANALES.clear()


def _cooldown_min() -> int:
    return int(os.getenv("ALERT_COOLDOWN_MIN", "60"))


def _url_panel() -> str:
    return os.getenv("PUBLIC_URL", "https://iotmangrove.info").rstrip("/")


def _redactar(alertas: list[dict]) -> tuple[str, str]:
    criticas = sum(1 for a in alertas if a["nivel"] == "CRITICO")
    asunto = f"[IoT-Mangrove] {len(alertas)} alerta(s)" + (f", {criticas} critica(s)" if criticas else "")
    lineas = ["Se detectaron valores fuera de umbral:", ""]
    for a in alertas:
        lineas.append(
            f"- [{a['nivel']}] Nodo {a['nodo']} ({a['ambito']}): {a['variable']} = {a['valor']} {a['unidad']}"
            f" - {a['umbral_mensaje'] or 'fuera de umbral'}"
        )
    lineas += ["", f"Revise y atienda las alertas en {_url_panel()}/alertas",
               "", "Puede cambiar estos avisos en su perfil del panel."]
    return asunto, "\n".join(lineas)


def notificar_alertas(alerta_ids: list[int]) -> None:
    """Avisa de las alertas indicadas. Pensada para ejecutarse en segundo
    plano despues de confirmar la ingesta; nunca lanza excepciones."""
    if not alerta_ids:
        return
    try:
        _notificar(alerta_ids)
    except Exception:  # noqa: BLE001 - un fallo aqui no debe afectar la ingesta
        log.exception("Error inesperado al notificar alertas %s", alerta_ids)


def _notificar(alerta_ids: list[int]) -> None:
    canal = _canales()["EMAIL"]
    with obtener_pool().connection() as db:
        alertas = db.execute(
            """SELECT al.id, al.mensaje, u.id AS umbral_id, u.nivel::text AS nivel, u.mensaje AS umbral_mensaje,
                      n.codigo::text AS nodo, a.codigo::text AS ambito,
                      v.codigo::text AS variable, m.valor, um.simbolo::text AS unidad
               FROM alerta al
               JOIN umbral u ON u.id = al.umbral_id
               JOIN medicion m ON m.id = al.medicion_id
               JOIN variable v ON v.id = m.variable_id
               JOIN unidad_medida um ON um.id = v.unidad_id
               JOIN lectura l ON l.id = m.lectura_id
               JOIN nodo n ON n.id = l.nodo_id
               JOIN ambito a ON a.id = n.ambito_id
               WHERE al.id = ANY(%s)
               ORDER BY al.id""",
            (alerta_ids,),
        ).fetchall()
        usuarios = db.execute(
            """SELECT id, email::text AS email, notificar_nivel::text AS nivel_min
               FROM usuario
               WHERE estado = TRUE AND notificar_alertas = TRUE AND email IS NOT NULL AND email <> ''"""
        ).fetchall()

        for usuario in usuarios:
            minimo = NIVELES.get(usuario["nivel_min"], 2)
            elegibles = [a for a in alertas if NIVELES.get(a["nivel"], 0) >= minimo]
            a_enviar: list[dict] = []
            for a in elegibles:
                repetida = db.execute(
                    """SELECT 1 FROM notificacion nt
                       JOIN alerta a2 ON a2.id = nt.alerta_id
                       JOIN medicion m2 ON m2.id = a2.medicion_id
                       JOIN lectura l2 ON l2.id = m2.lectura_id
                       WHERE nt.usuario_id = %s AND nt.canal = %s AND nt.situacion = 'ENVIADA'
                         AND a2.umbral_id = %s
                         AND l2.nodo_id = (SELECT l.nodo_id FROM medicion m JOIN lectura l ON l.id = m.lectura_id
                                           JOIN alerta al ON al.medicion_id = m.id WHERE al.id = %s)
                         AND nt.creado > now() - make_interval(mins => %s)
                       LIMIT 1""",
                    (usuario["id"], canal.nombre, a["umbral_id"], a["id"], _cooldown_min()),
                ).fetchone()
                if repetida:
                    _registrar(db, a["id"], usuario["id"], canal.nombre, usuario["email"], "OMITIDA", "antirrebote")
                else:
                    a_enviar.append(a)
            if not a_enviar:
                continue
            if not canal.configurado():
                for a in a_enviar:
                    _registrar(db, a["id"], usuario["id"], canal.nombre, usuario["email"], "OMITIDA", "SMTP no configurado")
                continue
            asunto, cuerpo = _redactar(a_enviar)
            try:
                canal.enviar(usuario["email"], asunto, cuerpo)
                situacion, detalle = "ENVIADA", None
            except Exception as exc:  # noqa: BLE001
                situacion, detalle = "FALLIDA", str(exc)[:250]
                log.warning("Fallo el envio a %s: %s", usuario["email"], exc)
            for a in a_enviar:
                _registrar(db, a["id"], usuario["id"], canal.nombre, usuario["email"], situacion, detalle)
        db.commit()


def _registrar(db: psycopg.Connection, alerta_id: int, usuario_id: int, canal: str,
               destino: str, situacion: str, detalle: str | None) -> None:
    db.execute(
        """INSERT INTO notificacion (alerta_id, usuario_id, canal, destino, situacion, detalle)
           VALUES (%s, %s, %s, %s, %s, %s)
           ON CONFLICT (alerta_id, usuario_id, canal) DO NOTHING""",
        (alerta_id, usuario_id, canal, destino, situacion, detalle),
    )


def enviar_prueba(destino: str) -> None:
    """Envia un correo de prueba (lanza excepcion si falla)."""
    canal = _canales()["EMAIL"]
    if not canal.configurado():
        raise RuntimeError("SMTP no configurado (defina SMTP_HOST)")
    canal.enviar(destino, "[IoT-Mangrove] Correo de prueba",
                 "Este es un correo de prueba de las notificaciones de IoT-Mangrove.")
