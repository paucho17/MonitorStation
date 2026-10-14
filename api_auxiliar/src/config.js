'use strict';

/**
 * Configuracion de la API auxiliar. Todos los valores se leen de variables
 * de entorno; ninguna credencial se escribe en el codigo fuente.
 */

function obligatoria(nombre) {
  const valor = process.env[nombre];
  if (!valor) {
    throw new Error(`Falta la variable de entorno ${nombre}`);
  }
  return valor;
}

const jwtSecreto = obligatoria('JWT_SECRET');
if (jwtSecreto.length < 32) {
  throw new Error('JWT_SECRET debe tener al menos 32 caracteres');
}

module.exports = {
  puerto: parseInt(process.env.PORT || '3000', 10),
  db: {
    host: obligatoria('DB_HOST'),
    port: parseInt(process.env.DB_PORT || '3306', 10),
    user: obligatoria('DB_USER'),
    password: obligatoria('DB_PASSWORD'),
    database: obligatoria('DB_NAME'),
    limiteConexiones: parseInt(process.env.DB_POOL_SIZE || '5', 10),
  },
  // Debe ser el mismo secreto que usa la API principal para firmar los JWT
  jwtSecreto,
  corsOrigenes: (process.env.CORS_ORIGINS || '')
    .split(',')
    .map((o) => o.trim())
    .filter(Boolean),
};
