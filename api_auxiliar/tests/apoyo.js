'use strict';

/**
 * Apoyo para pruebas sin MySQL: reemplaza el modulo ../src/db por un pool
 * falso cuyo contenido sale de los scripts SQL de db/auxiliar. Asi se prueba
 * el motor real del chatbot con la misma base de conocimiento que se despliega.
 */

const fs = require('fs');
const path = require('path');

const DIRECTORIO_SQL = path.join(__dirname, '..', '..', 'db', 'auxiliar');

/** Lee las tuplas (categoria, variable, pregunta, respuesta, palabras_clave) de los INSERT. */
function cargarConocimiento() {
  const filas = [];
  const referencias = {};
  for (const archivo of fs.readdirSync(DIRECTORIO_SQL).filter((f) => f.endsWith('.sql')).sort()) {
    const sql = fs.readFileSync(path.join(DIRECTORIO_SQL, archivo), 'utf8');
    for (const m of sql.matchAll(/\('([a-z0-9_]+)',\s*'([^']+)',\s*'([^']+)',\s*\n\s*'([^']+)',\s*\n\s*'([^']+)',\s*\n?\s*(NULL|[\d.]+),\s*(NULL|[\d.]+)/g)) {
      referencias[m[1]] = { unidad: m[3], min: m[6] === 'NULL' ? null : m[6], max: m[7] === 'NULL' ? null : m[7] };
    }
    const re = /\(\(SELECT id FROM categoria_conocimiento WHERE nombre='([^']+)'\),\s*\n?\s*(NULL|\(SELECT id FROM referencia_variable WHERE codigo_variable='([a-z0-9_]+)'\)),\s*\n\s*'([^']+)',\s*\n\s*'([^']+)',\s*\n\s*'([^']+)'\)/g;
    for (const m of sql.matchAll(re)) {
      const ref = m[3] ? referencias[m[3]] : null;
      filas.push({
        id: filas.length + 1, categoria: m[1], pregunta: m[4], respuesta: m[5], palabras_clave: m[6],
        codigo_variable: m[3] || null, unidad: ref ? ref.unidad : null,
        rango_normal_min: ref ? ref.min : null, rango_normal_max: ref ? ref.max : null,
      });
    }
  }
  return filas;
}

function instalarPoolFalso() {
  const conocimiento = cargarConocimiento();
  const registro = [];
  const pool = {
    async query(sql, params) {
      if (/FROM conocimiento_chatbot/.test(sql)) {
        return [conocimiento.map((f) => ({ ...f, categoria: f.categoria }))];
      }
      if (/INSERT INTO consulta_chatbot/.test(sql)) { registro.push(params); return [{}]; }
      return [[]];
    },
  };
  const ruta = require.resolve('../src/db');
  require.cache[ruta] = { id: ruta, filename: ruta, loaded: true, exports: { pool, traducirError: () => null } };
  return { conocimiento, registro };
}

module.exports = { instalarPoolFalso };
