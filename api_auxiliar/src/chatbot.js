'use strict';

const express = require('express');
const rateLimit = require('express-rate-limit');
const { pool } = require('./db');

/**
 * Motor de busqueda para el chatbot (Tidio u otro cliente).
 *
 * Recibe el texto de la pregunta, lo normaliza (minusculas, sin tildes ni
 * signos) y puntua cada entrada de la base de conocimiento:
 *   - 2 puntos por cada palabra que coincide con palabras_clave
 *   - 1 punto por cada palabra que coincide con el texto de la pregunta
 * Se devuelve la entrada de mayor puntaje si supera el minimo; en caso
 * contrario se responde con un mensaje por defecto. Cada consulta queda
 * registrada en consulta_chatbot.
 */

const PALABRAS_VACIAS = new Set([
  'el', 'la', 'los', 'las', 'de', 'del', 'que', 'cual', 'cuales', 'es', 'en', 'un', 'una', 'y', 'a',
  'para', 'por', 'como', 'se', 'mi', 'me', 'cuanto', 'cuando', 'son', 'al', 'lo', 'con', 'si', 'hay',
]);
const PUNTAJE_MINIMO = 2;
const MENSAJE_SIN_RESPUESTA =
  'No encontre información sobre esa pregunta. Puede consultar por pH, turbidez, TDS, temperatura, humedad, presion, eCO2, TVOC, humedad del suelo o alertas.';

/** Minusculas, sin tildes ni signos, sin palabras vacias y con plural simplificado. */
function tokenizar(texto) {
  return String(texto)
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter((t) => t && !PALABRAS_VACIAS.has(t))
    .map((t) => (t.length > 3 && t.endsWith('s') ? t.slice(0, -1) : t));
}

function puntuar(tokensConsulta, entrada) {
  const clave = new Set(tokenizar(entrada.palabras_clave));
  const pregunta = new Set(tokenizar(entrada.pregunta));
  let puntaje = 0;
  for (const t of new Set(tokensConsulta)) {
    if (clave.has(t)) puntaje += 2;
    else if (pregunta.has(t)) puntaje += 1;
  }
  return puntaje;
}

async function consultar(texto, origen) {
  const tokens = tokenizar(texto);
  const [entradas] = await pool.query(
    `SELECT k.id, k.pregunta, k.respuesta, k.palabras_clave, c.nombre AS categoria,
            r.codigo_variable, r.unidad, r.rango_normal_min, r.rango_normal_max
       FROM conocimiento_chatbot k
       JOIN categoria_conocimiento c ON c.id = k.categoria_id AND c.estado = 1
       LEFT JOIN referencia_variable r ON r.id = k.referencia_variable_id
      WHERE k.estado = 1`,
  );
  let mejor = null;
  let mejorPuntaje = 0;
  for (const e of entradas) {
    const p = puntuar(tokens, e);
    if (p > mejorPuntaje) { mejor = e; mejorPuntaje = p; }
  }
  const encontrada = mejor !== null && mejorPuntaje >= PUNTAJE_MINIMO;

  await pool.query(
    'INSERT INTO consulta_chatbot (conocimiento_id, texto_consulta, encontrada, origen) VALUES (?, ?, ?, ?)',
    [encontrada ? mejor.id : null, String(texto).slice(0, 500), encontrada ? 1 : 0, origen],
  );

  if (!encontrada) {
    return { encontrada: false, respuesta: MENSAJE_SIN_RESPUESTA };
  }
  return {
    encontrada: true,
    respuesta: mejor.respuesta,
    pregunta: mejor.pregunta,
    categoria: mejor.categoria,
    variable: mejor.codigo_variable
      ? {
          codigo: mejor.codigo_variable,
          unidad: mejor.unidad,
          rango_normal_min: mejor.rango_normal_min === null ? null : Number(mejor.rango_normal_min),
          rango_normal_max: mejor.rango_normal_max === null ? null : Number(mejor.rango_normal_max),
        }
      : null,
    puntaje: mejorPuntaje,
  };
}

const router = express.Router();

// Endpoint público: se limita la frecuencia para evitar abuso
router.use(rateLimit({
  windowMs: 60 * 1000,
  limit: 60,
  standardHeaders: true,
  legacyHeaders: false,
  message: { detail: 'Demasiadas consultas, intente de nuevo en un minuto' },
}));

const ORIGEN_VALIDO = /^[a-z0-9_-]{1,30}$/;

router.get('/consultar', async (req, res, next) => {
  try {
    const texto = (req.query.q || '').toString().trim();
    if (!texto) return res.status(400).json({ detail: 'Parametro q requerido' });
    const origen = ORIGEN_VALIDO.test(req.query.origen || '') ? req.query.origen : 'web';
    return res.json(await consultar(texto, origen));
  } catch (err) { return next(err); }
});

// Formato para webhooks: { "q": "texto", "origen": "tidio" }
router.post('/consultar', async (req, res, next) => {
  try {
    const texto = ((req.body && req.body.q) || '').toString().trim();
    if (!texto) return res.status(400).json({ detail: 'Campo q requerido' });
    const origen = ORIGEN_VALIDO.test((req.body && req.body.origen) || '') ? req.body.origen : 'tidio';
    return res.json(await consultar(texto, origen));
  } catch (err) { return next(err); }
});

module.exports = { router, tokenizar };
