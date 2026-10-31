#!/usr/bin/env bash
# Verifica la sintaxis de los sketches con g++ contra sustitutos de las bibliotecas
# del ESP32 (firmware/tests/stubs). Detecta errores de tipeo, firmas y tipos propios;
# NO sustituye la compilacion real con el Arduino IDE o arduino-cli, porque los
# sustitutos reproducen el API tal como se espera, no el codigo real de las bibliotecas.
# Uso: bash firmware/tests/verificar_sintaxis.sh
set -u
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
FALLOS=0
for ino in "$RAIZ"/*/*.ino; do
  carpeta="$(dirname "$ino")"
  salida="$(mktemp --suffix=.cpp)"
  { echo "#include <Arduino.h>"; cat "$ino"; } > "$salida"
  [ -f "$carpeta/secrets.h" ] || cp "$carpeta/secrets.h.example" "$carpeta/secrets.h" 2>/dev/null && BORRAR="$carpeta/secrets.h" || BORRAR=""
  if g++ -std=gnu++11 -fsyntax-only -Wall -Wextra -Wno-unused-parameter -Wno-unused-function -Wno-unused-variable \
       -I"$RAIZ/tests/stubs" -I"$RAIZ/libraries/IoTMangrove/src" -I"$carpeta" "$salida" 2> /tmp/sintaxis.log; then
    echo "OK   $(basename "$ino")"
  else
    echo "FALLA $(basename "$ino")"; cat /tmp/sintaxis.log | head -30; FALLOS=$((FALLOS+1))
  fi
  [ -n "$BORRAR" ] && rm -f "$BORRAR"
  rm -f "$salida"
done
exit $FALLOS
