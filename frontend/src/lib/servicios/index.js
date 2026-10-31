/** Registro de servicios CRUD por clave de tabla. Los servicios de datos estan en datos.js. */
import { api_usuarios } from './api_usuarios.js';
import { api_roles } from './api_roles.js';
import { api_modulos } from './api_modulos.js';
import { api_permisos } from './api_permisos.js';
import { api_zonas } from './api_zonas.js';
import { api_gateways } from './api_gateways.js';
import { api_nodos } from './api_nodos.js';
import { api_tipos_nodo } from './api_tipos_nodo.js';
import { api_ambitos } from './api_ambitos.js';
import { api_unidades } from './api_unidades.js';
import { api_variables } from './api_variables.js';
import { api_alias_variables } from './api_alias_variables.js';
import { api_sensores } from './api_sensores.js';
import { api_umbrales } from './api_umbrales.js';
import { api_alertas } from './api_alertas.js';
import { api_notificaciones } from './api_notificaciones.js';
import { api_zonas_riego } from './api_zonas_riego.js';
import { api_actuadores } from './api_actuadores.js';
import { api_programas_riego } from './api_programas_riego.js';
import { api_comandos_riego } from './api_comandos_riego.js';
import { api_eventos_riego } from './api_eventos_riego.js';

export const SERVICIOS = {
	usuarios: api_usuarios,
	roles: api_roles,
	modulos: api_modulos,
	permisos: api_permisos,
	zonas: api_zonas,
	gateways: api_gateways,
	nodos: api_nodos,
	tipos_nodo: api_tipos_nodo,
	ambitos: api_ambitos,
	unidades: api_unidades,
	variables: api_variables,
	alias_variables: api_alias_variables,
	sensores: api_sensores,
	umbrales: api_umbrales,
	alertas: api_alertas,
	notificaciones: api_notificaciones,
	zonas_riego: api_zonas_riego,
	actuadores: api_actuadores,
	programas_riego: api_programas_riego,
	comandos_riego: api_comandos_riego,
	eventos_riego: api_eventos_riego,
};
export { TABLAS, GRUPOS, claveDeTabla, urlDeTabla } from './tablas.js';
