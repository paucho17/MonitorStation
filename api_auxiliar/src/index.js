'use strict';

/**
 * IoT-Mangrove: API auxiliar (Express + MySQL).
 * Base de conocimiento del chatbot: categorias, fichas de variables,
 * preguntas frecuentes y bitacora de consultas.
 */

const cors = require('cors');
const express = require('express');
const helmet = require('helmet');
const config = require('./config');
const { pool, traducirError } = require('./db');
const { crearRouter } = require('./crud');
const recursos = require('./recursos');
const chatbot = require('./chatbot');

const app = express();
app.set('trust proxy', 1); // detras de Nginx
app.use(helmet());
if (config.corsOrigenes.length) {
  app.use(cors({ origin: config.corsOrigenes }));
}
app.use(express.json({ limit: '100kb' }));

app.get('/salud', async (_req, res) => {
  try {
    await pool.query('SELECT 1');
    res.json({ estado: 'ok' });
  } catch (err) {
    res.status(503).json({ estado: 'sin conexion a la base de datos' });
  }
});

app.get('/', (_req, res) => {
  res.json({
    servicio: 'IoT-Mangrove API auxiliar',
    recursos: recursos.map((r) => `/${r.ruta}`),
    chatbot: ['GET /chatbot/consultar?q=texto', 'POST /chatbot/consultar {"q": "texto"}'],
    salud: '/salud',
  });
});

// Ficha de una variable por su codigo (p. ej. /referencias/codigo/ph)
app.get('/referencias/codigo/:codigo', async (req, res, next) => {
  try {
    const [filas] = await pool.query(
      'SELECT * FROM referencia_variable WHERE codigo_variable = ? AND estado = 1',
      [req.params.codigo.toLowerCase()],
    );
    if (!filas.length) return res.status(404).json({ detail: 'Variable no encontrada' });
    const { estado, ...ficha } = filas[0];
    return res.json({ ...ficha, estado: Boolean(estado) });
  } catch (err) { return next(err); }
});

app.use('/chatbot', chatbot.router);
for (const recurso of recursos) {
  app.use(`/${recurso.ruta}`, crearRouter(recurso));
}

app.use((_req, res) => res.status(404).json({ detail: 'Ruta no encontrada' }));

// Manejo central de errores
// eslint-disable-next-line no-unused-vars
app.use((err, _req, res, _next) => {
  if (err.type === 'entity.parse.failed') {
    return res.status(400).json({ detail: 'JSON inválido' });
  }
  const traducido = traducirError(err);
  if (traducido) return res.status(traducido.estado).json({ detail: traducido.mensaje });
  console.error('[error]', err);
  return res.status(500).json({ detail: 'Error interno del servidor' });
});

if (require.main === module) {
  app.listen(config.puerto, () => {
    console.log(`[api-auxiliar] escuchando en el puerto ${config.puerto}`);
  });
}

module.exports = app;
