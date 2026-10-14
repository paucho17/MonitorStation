"""Verificación automática de las reglas del proyecto IoT-Mangrove.

Uso (desde la raíz del proyecto):
    python3 scripts/verificar_reglas.py

Comprueba:
  1. Ausencia de emojis en código y documentación.
  2. Que toda tabla SQL tenga llave primaria y los campos estado, creado y actualizado.
  3. Que existan las tablas rol, usuario, modulo y modulo_rol, y el mínimo de tablas por base.
  4. Ausencia de credenciales conocidas o escritas directamente en archivos de configuración.
  5. Que cada archivo de código tenga una descripción de módulo al inicio.
  6. Que cada módulo de api_principal/app tenga su documento .md al lado.
  7. Que el archivo .env no esté dentro del proyecto empaquetado.

Termina con código 1 si alguna comprobación falla.
"""

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
IGNORAR = {"node_modules", "__pycache__", ".git", "certbot"}
EXT_CODIGO = {".py", ".js", ".sql", ".html", ".css", ".yml", ".yaml", ".sh", ".md", ".conf"}
# Rangos de puntos de código Unicode de emojis (escritos como números para que este
# archivo no contenga emojis literales)
RANGOS_EMOJI = ((0x1F300, 0x1FAFF), (0x2600, 0x27BF), (0x2B50, 0x2B50))
EMOJI = re.compile("[" + "".join(f"{chr(a)}-{chr(b)}" for a, b in RANGOS_EMOJI) + "]")
CAMPOS_AUDITORIA = ("estado", "creado", "actualizado")
TABLAS_OBLIGATORIAS = {"rol", "usuario", "modulo", "modulo_rol"}
MINIMO_TABLAS = {"principal": 12, "auxiliar": 3}
SECRETOS_CONOCIDOS = ("admin123", "TuPasswordSegura123", "QeTuO_135", "paucho17", "loco123")

fallos: list[str] = []


def archivos(extensiones: set[str]):
    """Recorre el proyecto omitiendo carpetas generadas."""
    for ruta in sorted(RAIZ.rglob("*")):
        if ruta.is_file() and ruta.suffix in extensiones and not (IGNORAR & set(ruta.parts)):
            yield ruta


def relativa(ruta: Path) -> str:
    return str(ruta.relative_to(RAIZ))


def revisar_emojis() -> None:
    for ruta in archivos(EXT_CODIGO):
        for n, linea in enumerate(ruta.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if EMOJI.search(linea):
                fallos.append(f"Emoji en {relativa(ruta)}:{n}")


def extraer_tablas(sql: str) -> dict[str, str]:
    """Devuelve {nombre_tabla: cuerpo} de cada CREATE TABLE."""
    tablas = {}
    for m in re.finditer(r"CREATE TABLE\s+(?:IF NOT EXISTS\s+)?`?(\w+)`?\s*\(", sql, re.I):
        nivel, i = 1, m.end()
        while i < len(sql) and nivel:
            nivel += {"(": 1, ")": -1}.get(sql[i], 0)
            i += 1
        tablas[m.group(1).lower()] = sql[m.end(): i - 1]
    return tablas


def revisar_tablas() -> None:
    for base in ("principal", "auxiliar"):
        tablas: dict[str, str] = {}
        for ruta in (RAIZ / "db" / base).glob("*.sql"):
            tablas.update(extraer_tablas(ruta.read_text(encoding="utf-8")))
        for nombre, cuerpo in tablas.items():
            if not re.search(r"PRIMARY KEY", cuerpo, re.I):
                fallos.append(f"Tabla {nombre} ({base}) sin llave primaria")
            for campo in CAMPOS_AUDITORIA:
                if not re.search(rf"^\s*`?{campo}`?\s", cuerpo, re.M):
                    fallos.append(f"Tabla {nombre} ({base}) sin el campo '{campo}'")
        if len(tablas) < MINIMO_TABLAS[base]:
            fallos.append(f"Base {base}: {len(tablas)} tablas, se exigen al menos {MINIMO_TABLAS[base]}")
        if base == "principal":
            faltan = TABLAS_OBLIGATORIAS - set(tablas)
            if faltan:
                fallos.append(f"Faltan tablas obligatorias: {', '.join(sorted(faltan))}")
        print(f"Base {base}: {len(tablas)} tablas revisadas")


def revisar_secretos() -> None:
    patron_asignacion = re.compile(
        r"""(password|passwd|secret|api_key)\s*[:=]\s*["']([^"'$\s{}][^"']{5,})["']""", re.I
    )
    for ruta in archivos(EXT_CODIGO):
        if ruta.name == "verificar_reglas.py":
            continue
        for n, linea in enumerate(ruta.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if ruta.suffix != ".md" and any(s in linea for s in SECRETOS_CONOCIDOS):
                fallos.append(f"Credencial conocida en {relativa(ruta)}:{n}")
            elif ruta.suffix in {".py", ".js", ".yml", ".yaml", ".sql"} and patron_asignacion.search(linea):
                if "CAMBIAR" not in linea and "prueba" not in ruta.name:
                    fallos.append(f"Posible credencial escrita en {relativa(ruta)}:{n}")
    if (RAIZ / ".env").exists():
        fallos.append(".env presente dentro del proyecto: no debe empaquetarse ni versionarse")


def revisar_documentacion() -> None:
    for ruta in archivos({".py", ".js"}):
        inicio = ruta.read_text(encoding="utf-8").lstrip()[:200]
        if ruta.name == "__init__.py":
            continue
        if not (inicio.startswith(('"""', "'use strict'", "#!", "/*"))):
            fallos.append(f"{relativa(ruta)} sin descripción de módulo al inicio")
        elif inicio.startswith("'use strict'") and "/**" not in ruta.read_text(encoding="utf-8")[:300]:
            fallos.append(f"{relativa(ruta)} sin descripción de módulo tras 'use strict'")


def revisar_documentos_de_modulo() -> None:
    """Cada módulo Python de la API principal debe tener su .md al lado."""
    base = Path(__file__).resolve().parent.parent / "api_principal" / "app"
    for ruta in sorted(base.rglob("*.py")):
        if ruta.name == "__init__.py":
            continue
        if not ruta.with_suffix(".md").exists():
            fallos.append(f"{relativa(ruta)} sin documento de módulo (.md junto al archivo)")


if __name__ == "__main__":
    revisar_emojis()
    revisar_tablas()
    revisar_secretos()
    revisar_documentacion()
    revisar_documentos_de_modulo()
    if fallos:
        print(f"\n{len(fallos)} problema(s):")
        for f in fallos:
            print(" -", f)
        sys.exit(1)
    print("Todas las comprobaciones automáticas pasaron.")
