'use strict';

/** Pruebas del chatbot con la base de conocimiento real (node --test tests/). */

const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const express = require('express');
const { instalarPoolFalso } = require('./apoyo');

const { conocimiento, registro } = instalarPoolFalso();
const chatbot = require('../src/chatbot');

async function servidor() {
  const app = express();
  app.use(express.json());
  app.use('/chatbot', chatbot.router);
  const srv = http.createServer(app);
  await new Promise((r) => srv.listen(0, r));
  const base = `http://127.0.0.1:${srv.address().port}/chatbot/consultar`;
  return { srv, preguntar: async (q) => (await fetch(base, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ q, origen: 'web' }) })).json() };
}

test('la base de conocimiento incluye el vivero y el riego', () => {
  const categorias = new Set(conocimiento.map((c) => c.categoria));
  assert.ok(categorias.has('Riego') && categorias.has('Vivero'));
  assert.ok(conocimiento.length >= 22, `entradas: ${conocimiento.length}`);
});

const CASOS = [
  ['¿Cuál es el pH normal del agua?', 'rango de referencia del proyecto es de 6.5'],
  ['como funciona el riego automatico', 'humedad del suelo del vivero'],
  ['que modos de riego hay', 'cuatro modos'],
  ['puedo abrir una valvula desde la pagina', 'modo Manual'],
  ['que pasa si el tanque esta bajo', 'bloquea'],
  ['para que sirve el sensor de CO2', 'SCD41'],
  ['que son pm2.5 y pm10', 'PM2.5'],
  ['diferencia entre manglar vivero y riego', 'ámbitos'],
  ['temperatura del suelo', '42'],
];

for (const [pregunta, esperado] of CASOS) {
  test(`responde: ${pregunta}`, async () => {
    const { srv, preguntar } = await servidor();
    try {
      const r = await preguntar(pregunta);
      assert.equal(r.encontrada, true, JSON.stringify(r));
      assert.match(r.respuesta, new RegExp(esperado.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i'));
    } finally { srv.close(); }
  });
}

test('pregunta sin relacion devuelve el mensaje por defecto y se registra', async () => {
  const { srv, preguntar } = await servidor();
  try {
    const antes = registro.length;
    const r = await preguntar('quien gano el partido de ayer');
    assert.equal(r.encontrada, false);
    assert.match(r.respuesta, /riego/i);
    assert.equal(registro.length, antes + 1);
  } finally { srv.close(); }
});
