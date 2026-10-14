'use strict';

const express = require('express');
const { pool, traducirError } = require('./db');
const { requerirRol } = require('./auth');

/**
 * Fabrica de endpoints CRUD con eliminacion logica (campo estado).
 *
 *   GET     /<ruta>                  lista (filtros y paginacion)
 *   GET     /<ruta>/:id              detalle
 *   POST    /<ruta>                  crea
 *   PUT     /<ruta>/:id              actualiza parcialmente
 *   DELETE  /<ruta>/:id              eliminacion logica (estado = 0)
 *   POST    /<ruta>/:id/restaurar    reactiva (estado = 1)
 *
 * Los campos creado y actualizado los administra el motor de MySQL.
 */

const ROLES_ESCRITURA = ['admin', 'operador'];

/** Valida y convierte el cuerpo segun la definicion de campos. */
function validar(recurso, cuerpo, crear) {
  const valores = {};
  const errores = [];
  for (const c of recurso.campos) {
    if (!crear && c.editable === false) continue;
    const presente = Object.prototype.hasOwnProperty.call(cuerpo, c.nombre);
    if (!presente) {
      if (crear && c.requerido) errores.push(`${c.nombre} es obligatorio`);
      continue;
    }
    let valor = cuerpo[c.nombre];
    if (valor === null || valor === '') {
      if (c.requerido) errores.push(`${c.nombre} no puede estar vacío`);
      else valores[c.nombre] = null;
      continue;
    }
    switch (c.tipo) {
      case 'texto':
        if (typeof valor !== 'string') { errores.push(`${c.nombre} debe ser texto`); continue; }
        valor = valor.trim();
        if (c.max && valor.length > c.max) { errores.push(`${c.nombre} supera ${c.max} caracteres`); continue; }
        break;
      case 'entero':
        valor = Number(valor);
        if (!Number.isInteger(valor)) { errores.push(`${c.nombre} debe ser un entero`); continue; }
        break;
      case 'numero':
        valor = Number(valor);
        if (!Number.isFinite(valor)) { errores.push(`${c.nombre} debe ser numérico`); continue; }
        break;
      case 'booleano':
        valor = (valor === true || valor === 1 || valor === '1' || valor === 'true') ? 1 : 0;
        break;
      default:
        break;
    }
    valores[c.nombre] = valor;
  }
  return { valores, errores };
}

function crearRouter(recurso) {
  const router = express.Router();
  const columnas = ['id', ...recurso.campos.map((c) => c.nombre), 'estado', 'creado', 'actualizado'];
  const lista = columnas.map((c) => `\`${c}\``).join(', ');
  const tabla = `\`${recurso.tabla}\``;
  const booleanos = new Set(['estado', ...recurso.campos.filter((c) => c.tipo === 'booleano').map((c) => c.nombre)]);
  const rolesEscritura = recurso.rolesEscritura || ROLES_ESCRITURA;
  const rolesEliminar = recurso.rolesEliminar || ROLES_ESCRITURA;
  const lectura = recurso.lecturaPublica ? [] : [requerirRol(...ROLES_ESCRITURA)];

  const formatear = (fila) => {
    const salida = { ...fila };
    for (const b of booleanos) salida[b] = Boolean(salida[b]);
    return salida;
  };

  const obtener = async (id) => {
    const [filas] = await pool.query(`SELECT ${lista} FROM ${tabla} WHERE id = ?`, [id]);
    return filas.length ? formatear(filas[0]) : null;
  };

  const idValido = (req, res, next) => {
    if (!/^\d+$/.test(req.params.id)) return res.status(400).json({ detail: 'Identificador inválido' });
    return next();
  };

  // Rutas fijas antes de las parametrizadas
  router.get('/', ...lectura, async (req, res, next) => {
    try {
      const condiciones = [];
      const parametros = [];
      if (req.query.incluir_inactivos !== 'true') condiciones.push('estado = 1');
      for (const f of recurso.filtros || []) {
        if (req.query[f] !== undefined) {
          condiciones.push(`\`${f}\` = ?`);
          parametros.push(req.query[f]);
        }
      }
      const donde = condiciones.length ? `WHERE ${condiciones.join(' AND ')}` : '';
      const limite = Math.min(Math.max(parseInt(req.query.limite, 10) || 100, 1), 500);
      const desplazamiento = Math.max(parseInt(req.query.desplazamiento, 10) || 0, 0);
      const sentido = recurso.ordenDescendente ? 'DESC' : 'ASC';
      const [[{ total }]] = await pool.query(`SELECT COUNT(*) AS total FROM ${tabla} ${donde}`, parametros);
      const [filas] = await pool.query(
        `SELECT ${lista} FROM ${tabla} ${donde} ORDER BY id ${sentido} LIMIT ? OFFSET ?`,
        [...parametros, limite, desplazamiento],
      );
      res.json({ total, limite, desplazamiento, datos: filas.map(formatear) });
    } catch (err) { next(err); }
  });

  router.get('/:id', ...lectura, idValido, async (req, res, next) => {
    try {
      const fila = await obtener(req.params.id);
      if (!fila) return res.status(404).json({ detail: 'Registro no encontrado' });
      return res.json(fila);
    } catch (err) { return next(err); }
  });

  if (recurso.permitirCrear !== false) {
    router.post('/', requerirRol(...rolesEscritura), async (req, res, next) => {
      try {
        const { valores, errores } = validar(recurso, req.body || {}, true);
        if (errores.length) return res.status(400).json({ detail: errores.join('; ') });
        const nombres = Object.keys(valores);
        if (!nombres.length) return res.status(400).json({ detail: 'Cuerpo vacío' });
        const [resultado] = await pool.query(
          `INSERT INTO ${tabla} (${nombres.map((n) => `\`${n}\``).join(', ')}) VALUES (${nombres.map(() => '?').join(', ')})`,
          Object.values(valores),
        );
        return res.status(201).json(await obtener(resultado.insertId));
      } catch (err) { return next(err); }
    });
  }

  if (recurso.permitirEditar !== false) {
    router.put('/:id', requerirRol(...rolesEscritura), idValido, async (req, res, next) => {
      try {
        if (!(await obtener(req.params.id))) return res.status(404).json({ detail: 'Registro no encontrado' });
        const { valores, errores } = validar(recurso, req.body || {}, false);
        if (errores.length) return res.status(400).json({ detail: errores.join('; ') });
        const nombres = Object.keys(valores);
        if (!nombres.length) return res.status(400).json({ detail: 'No se enviaron campos para actualizar' });
        await pool.query(
          `UPDATE ${tabla} SET ${nombres.map((n) => `\`${n}\` = ?`).join(', ')} WHERE id = ?`,
          [...Object.values(valores), req.params.id],
        );
        return res.json(await obtener(req.params.id));
      } catch (err) { return next(err); }
    });
  }

  router.delete('/:id', requerirRol(...rolesEliminar), idValido, async (req, res, next) => {
    try {
      if (!(await obtener(req.params.id))) return res.status(404).json({ detail: 'Registro no encontrado' });
      await pool.query(`UPDATE ${tabla} SET estado = 0 WHERE id = ?`, [req.params.id]);
      return res.json(await obtener(req.params.id));
    } catch (err) { return next(err); }
  });

  router.post('/:id/restaurar', requerirRol(...rolesEscritura), idValido, async (req, res, next) => {
    try {
      if (!(await obtener(req.params.id))) return res.status(404).json({ detail: 'Registro no encontrado' });
      await pool.query(`UPDATE ${tabla} SET estado = 1 WHERE id = ?`, [req.params.id]);
      return res.json(await obtener(req.params.id));
    } catch (err) { return next(err); }
  });

  return router;
}

module.exports = { crearRouter };
