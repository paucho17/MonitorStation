"""Configuracion de la API principal.

Todos los valores sensibles se leen de variables de entorno; ninguna
credencial se escribe en el codigo fuente.
"""

import os


class ConfiguracionError(RuntimeError):
    """Se lanza cuando falta una variable de entorno obligatoria."""


def _obligatoria(nombre: str) -> str:
    valor = os.getenv(nombre)
    if not valor:
        raise ConfiguracionError(f"Falta la variable de entorno {nombre}")
    return valor


def _lista(nombre: str, defecto: str = "") -> list[str]:
    return [v.strip() for v in os.getenv(nombre, defecto).split(",") if v.strip()]


class Configuracion:
    """Valores de configuracion leidos una sola vez al iniciar."""

    def __init__(self) -> None:
        # Base de datos PostgreSQL
        self.db_host = _obligatoria("DB_HOST")
        self.db_puerto = int(os.getenv("DB_PORT", "5432"))
        self.db_nombre = _obligatoria("DB_NAME")
        self.db_usuario = _obligatoria("DB_USER")
        self.db_clave = _obligatoria("DB_PASSWORD")
        self.db_sslmode = os.getenv("DB_SSLMODE", "prefer")
        self.db_pool_max = int(os.getenv("DB_POOL_SIZE", "5"))

        # JWT
        self.jwt_secreto = _obligatoria("JWT_SECRET")
        if len(self.jwt_secreto) < 32:
            raise ConfiguracionError("JWT_SECRET debe tener al menos 32 caracteres")
        self.jwt_algoritmo = "HS256"
        self.jwt_minutos = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

        # Usuario administrador inicial (se crea solo si no existe)
        self.admin_usuario = os.getenv("ADMIN_USERNAME", "admin")
        self.admin_email = os.getenv("ADMIN_EMAIL") or None
        self.admin_clave = _obligatoria("ADMIN_PASSWORD")

        # Gateway LoRa inicial: su clave de API se sincroniza al iniciar
        self.gateway_codigo = os.getenv("GATEWAY_CODE", "0XDD").upper()
        self.gateway_clave = os.getenv("GATEWAY_API_KEY", "")

        # Registro público de usuarios (siempre con rol "consulta")
        self.permitir_registro = os.getenv("ALLOW_REGISTRATION", "true").lower() == "true"

        # CORS
        self.cors_origenes = _lista("CORS_ORIGINS")


def cargar() -> Configuracion:
    """Crea la configuracion (separado para facilitar las pruebas)."""
    return Configuracion()
