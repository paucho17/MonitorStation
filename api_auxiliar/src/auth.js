'use strict';

const jwt = require('jsonwebtoken');
const config = require('./config');

/**
 * Middleware que exige un JWT valido emitido por la API principal
 * (mismo secreto, algoritmo HS256) y que el rol este permitido.
 *
 * Nota de diseno: esta API verifica firma y expiracion del token, pero no
 * consulta la tabla de sesiones de la base principal; un token revocado
 * con logout sigue siendo valido aqui hasta que expire.
 */
function requerirRol(...rolesPermitidos) {
  return (req, res, next) => {
    const cabecera = req.headers.authorization || '';
    const [esquema, token] = cabecera.split(' ');
    if (esquema !== 'Bearer' || !token) {
      return res.status(401).json({ detail: 'Token requerido' });
    }
    let carga;
    try {
      carga = jwt.verify(token, config.jwtSecreto, { algorithms: ['HS256'] });
    } catch (err) {
      const mensaje = err.name === 'TokenExpiredError' ? 'Token expirado' : 'Token inválido';
      return res.status(401).json({ detail: mensaje });
    }
    if (!rolesPermitidos.includes(carga.rol)) {
      return res.status(403).json({ detail: 'Rol sin permiso para esta operacion' });
    }
    req.usuario = carga;
    return next();
  };
}

module.exports = { requerirRol };
