'use strict';

const mysql = require('mysql2/promise');
const config = require('./config');

/** Pool de conexiones a MySQL (todas las fechas en UTC). */
const pool = mysql.createPool({
  host: config.db.host,
  port: config.db.port,
  user: config.db.user,
  password: config.db.password,
  database: config.db.database,
  waitForConnections: true,
  connectionLimit: config.db.limiteConexiones,
  charset: 'utf8mb4',
  timezone: 'Z',
});

/**
 * Traduce un error de MySQL en un objeto {estado, mensaje} para el cliente.
 * Devuelve null si el error no es de base de datos conocido.
 */
function traducirError(err) {
  switch (err && err.code) {
    case 'ER_DUP_ENTRY':
      return { estado: 409, mensaje: 'Ya existe un registro con ese valor único' };
    case 'ER_NO_REFERENCED_ROW_2':
      return { estado: 400, mensaje: 'Referencia inválida: el registro relacionado no existe' };
    case 'ER_BAD_NULL_ERROR':
      return { estado: 400, mensaje: 'Falta un campo obligatorio' };
    case 'ER_DATA_TOO_LONG':
    case 'ER_TRUNCATED_WRONG_VALUE':
    case 'ER_WARN_DATA_OUT_OF_RANGE':
      return { estado: 400, mensaje: 'Valor con formato inválido o demasiado largo' };
    default:
      return null;
  }
}

module.exports = { pool, traducirError };
