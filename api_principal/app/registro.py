"""Registro de modulos funcionales de la API.

Cada modulo agrupa los routers y los recursos CRUD de una parte del
sistema. main.py solo recorre MODULOS, de modo que sumar una funcion nueva
(por ejemplo un modulo de sensores de pesca o de energia) consiste en:

  1. Crear su router y/o su lista de Recurso.
  2. Declarar aqui un ModuloApi.
  3. Agregar su migracion SQL (tablas, modulo de permisos y semillas).

El orden importa: el front-end estatico se monta despues de todos.
"""

from dataclasses import dataclass, field

from fastapi import APIRouter

from app.crud import Recurso
from app.recursos import RECURSOS
from app.recursos_riego import RECURSOS_RIEGO
from app.routers import auth, datos, gateways, ingesta, riego


@dataclass
class ModuloApi:
    """Conjunto de routers y recursos CRUD que se publican juntos."""

    nombre: str
    routers: list[APIRouter] = field(default_factory=list)
    recursos: list[Recurso] = field(default_factory=list)


MODULOS: list[ModuloApi] = [
    ModuloApi("nucleo", routers=[auth.router, ingesta.router, datos.router, gateways.router],
              recursos=RECURSOS),
    ModuloApi("riego", routers=[riego.router], recursos=RECURSOS_RIEGO),
]
