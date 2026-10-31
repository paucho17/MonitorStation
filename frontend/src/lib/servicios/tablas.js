/**
 * Catalogo de tablas administrables desde el panel.
 *
 * Cada entrada describe un recurso de la API: su modulo de permisos, las
 * columnas de la lista y los campos del formulario. Un campo de tipo
 * "relacion" se llena con las filas de otra tabla (opciones = clave de
 * este mismo catalogo, etiqueta = campo que se muestra). Agregar una tabla
 * nueva al panel es agregar una entrada aqui y su servicio api_<tabla>.js.
 */

/** @typedef {{nombre:string, etiqueta:string, tipo:'texto'|'numero'|'bool'|'relacion'|'seleccion'|'clave'|'hora', requerido?:boolean, tabla?:string, mostrar?:string, opciones?:string[], ayuda?:string, soloCrear?:boolean, ayudaMin?:number}} Campo */
/** @typedef {{ruta:string, modulo:string, titulo:string, descripcion:string, grupo:string, columnas:string[], campos:Campo[], soloLectura?:boolean, soloEstado?:boolean}} Tabla */

/** @type {Record<string, Tabla>} */
export const TABLAS = {
	usuarios: {
		ruta: 'usuarios', modulo: 'usuarios', titulo: 'Usuarios', grupo: 'Seguridad',
		descripcion: 'Cuentas del sistema, su rol y sus avisos de alertas.',
		columnas: ['id', 'username', 'email', 'nombre_completo', 'rol_id', 'notificar_alertas', 'estado'],
		campos: [
			{ nombre: 'username', etiqueta: 'Usuario', tipo: 'texto', requerido: true },
			{ nombre: 'email', etiqueta: 'Correo', tipo: 'texto' },
			{ nombre: 'nombre_completo', etiqueta: 'Nombre completo', tipo: 'texto' },
			{ nombre: 'rol_id', etiqueta: 'Rol', tipo: 'relacion', tabla: 'roles', mostrar: 'nombre', requerido: true },
			{ nombre: 'password', etiqueta: 'Contrasena', tipo: 'clave', ayuda: 'Minimo 6 caracteres. Vacio al editar = no cambia.' },
			{ nombre: 'notificar_alertas', etiqueta: 'Avisar alertas por correo', tipo: 'bool' },
			{ nombre: 'notificar_nivel', etiqueta: 'Nivel minimo del aviso', tipo: 'seleccion', opciones: ['CRITICO', 'ADVERTENCIA'] }
		]
	},
	roles: {
		ruta: 'roles', modulo: 'roles', titulo: 'Roles', grupo: 'Seguridad',
		descripcion: 'Perfiles de acceso: admin, operador, vivero, consulta.',
		columnas: ['id', 'nombre', 'descripcion', 'estado'],
		campos: [
			{ nombre: 'nombre', etiqueta: 'Nombre', tipo: 'texto', requerido: true },
			{ nombre: 'descripcion', etiqueta: 'Descripcion', tipo: 'texto' }
		]
	},
	modulos: {
		ruta: 'modulos', modulo: 'modulos', titulo: 'Modulos', grupo: 'Seguridad',
		descripcion: 'Recursos sobre los que se asignan permisos.',
		columnas: ['id', 'nombre', 'ruta', 'descripcion', 'estado'],
		campos: [
			{ nombre: 'nombre', etiqueta: 'Nombre', tipo: 'texto', requerido: true },
			{ nombre: 'ruta', etiqueta: 'Ruta', tipo: 'texto', requerido: true },
			{ nombre: 'descripcion', etiqueta: 'Descripcion', tipo: 'texto' }
		]
	},
	permisos: {
		ruta: 'permisos', modulo: 'permisos', titulo: 'Permisos', grupo: 'Seguridad',
		descripcion: 'Que puede hacer cada rol en cada modulo (leer, crear, editar, eliminar).',
		columnas: ['id', 'rol_id', 'modulo_id', 'puede_leer', 'puede_crear', 'puede_editar', 'puede_eliminar', 'estado'],
		campos: [
			{ nombre: 'rol_id', etiqueta: 'Rol', tipo: 'relacion', tabla: 'roles', mostrar: 'nombre', requerido: true, soloCrear: true },
			{ nombre: 'modulo_id', etiqueta: 'Modulo', tipo: 'relacion', tabla: 'modulos', mostrar: 'nombre', requerido: true, soloCrear: true },
			{ nombre: 'puede_leer', etiqueta: 'Leer', tipo: 'bool' },
			{ nombre: 'puede_crear', etiqueta: 'Crear', tipo: 'bool' },
			{ nombre: 'puede_editar', etiqueta: 'Editar', tipo: 'bool' },
			{ nombre: 'puede_eliminar', etiqueta: 'Eliminar', tipo: 'bool' }
		]
	},
	zonas: {
		ruta: 'zonas', modulo: 'zonas', titulo: 'Zonas de manglar', grupo: 'Infraestructura',
		descripcion: 'Areas geograficas donde se instalan gateways y nodos.',
		columnas: ['id', 'nombre', 'municipio', 'latitud', 'longitud', 'estado'],
		campos: [
			{ nombre: 'nombre', etiqueta: 'Nombre', tipo: 'texto', requerido: true },
			{ nombre: 'descripcion', etiqueta: 'Descripcion', tipo: 'texto' },
			{ nombre: 'municipio', etiqueta: 'Municipio', tipo: 'texto' },
			{ nombre: 'latitud', etiqueta: 'Latitud', tipo: 'numero' },
			{ nombre: 'longitud', etiqueta: 'Longitud', tipo: 'numero' }
		]
	},
	gateways: {
		ruta: 'gateways', modulo: 'gateways', titulo: 'Gateways', grupo: 'Infraestructura',
		descripcion: 'Puertas de enlace LoRa. La clave de API se muestra una sola vez al crearlas.',
		columnas: ['id', 'codigo', 'nombre', 'zona_id', 'ultima_conexion', 'estado'],
		campos: [
			{ nombre: 'codigo', etiqueta: 'Codigo', tipo: 'texto', requerido: true, soloCrear: true, ayuda: 'Direccion LoRa del gateway, p. ej. 0xDD' },
			{ nombre: 'nombre', etiqueta: 'Nombre', tipo: 'texto', requerido: true },
			{ nombre: 'zona_id', etiqueta: 'Zona', tipo: 'relacion', tabla: 'zonas', mostrar: 'nombre' }
		]
	},
	nodos: {
		ruta: 'nodos', modulo: 'nodos', titulo: 'Nodos', grupo: 'Infraestructura',
		descripcion: 'Estaciones de medicion LoRa del manglar, el vivero y el riego.',
		columnas: ['id', 'codigo', 'nombre', 'tipo_nodo_id', 'ambito_id', 'zona_id', 'hardware', 'estado'],
		campos: [
			{ nombre: 'codigo', etiqueta: 'Codigo', tipo: 'texto', requerido: true, ayuda: 'Direccion LoRa, p. ej. 0xAA' },
			{ nombre: 'nombre', etiqueta: 'Nombre', tipo: 'texto' },
			{ nombre: 'tipo_nodo_id', etiqueta: 'Tipo', tipo: 'relacion', tabla: 'tipos_nodo', mostrar: 'nombre', requerido: true },
			{ nombre: 'ambito_id', etiqueta: 'Ambito', tipo: 'relacion', tabla: 'ambitos', mostrar: 'nombre', requerido: true },
			{ nombre: 'zona_id', etiqueta: 'Zona', tipo: 'relacion', tabla: 'zonas', mostrar: 'nombre' },
			{ nombre: 'gateway_id', etiqueta: 'Gateway', tipo: 'relacion', tabla: 'gateways', mostrar: 'codigo' },
			{ nombre: 'hardware', etiqueta: 'Hardware', tipo: 'texto' }
		]
	},
	tipos_nodo: {
		ruta: 'tipos-nodo', modulo: 'tipos-nodo', titulo: 'Tipos de nodo', grupo: 'Infraestructura',
		descripcion: 'WATER, SOIL, AMB y RIEGO.',
		columnas: ['id', 'codigo', 'nombre', 'descripcion', 'estado'],
		campos: [
			{ nombre: 'codigo', etiqueta: 'Codigo', tipo: 'texto', requerido: true },
			{ nombre: 'nombre', etiqueta: 'Nombre', tipo: 'texto', requerido: true },
			{ nombre: 'descripcion', etiqueta: 'Descripcion', tipo: 'texto' }
		]
	},
	ambitos: {
		ruta: 'ambitos', modulo: 'ambitos', titulo: 'Ambitos', grupo: 'Infraestructura',
		descripcion: 'Dominios de monitoreo: MANGLAR, VIVERO, RIEGO.',
		columnas: ['id', 'codigo', 'nombre', 'orden', 'estado'],
		campos: [
			{ nombre: 'codigo', etiqueta: 'Codigo', tipo: 'texto', requerido: true },
			{ nombre: 'nombre', etiqueta: 'Nombre', tipo: 'texto', requerido: true },
			{ nombre: 'descripcion', etiqueta: 'Descripcion', tipo: 'texto' },
			{ nombre: 'orden', etiqueta: 'Orden', tipo: 'numero' }
		]
	},
	unidades: {
		ruta: 'unidades', modulo: 'unidades', titulo: 'Unidades de medida', grupo: 'Catalogos',
		descripcion: 'Simbolos y nombres de las unidades.',
		columnas: ['id', 'simbolo', 'nombre', 'estado'],
		campos: [
			{ nombre: 'simbolo', etiqueta: 'Simbolo', tipo: 'texto', requerido: true },
			{ nombre: 'nombre', etiqueta: 'Nombre', tipo: 'texto', requerido: true }
		]
	},
	variables: {
		ruta: 'variables', modulo: 'variables', titulo: 'Variables', grupo: 'Catalogos',
		descripcion: 'Magnitudes medidas por los sensores y su rango fisico valido.',
		columnas: ['id', 'codigo', 'nombre', 'unidad_id', 'rango_min', 'rango_max', 'estado'],
		campos: [
			{ nombre: 'codigo', etiqueta: 'Codigo', tipo: 'texto', requerido: true },
			{ nombre: 'nombre', etiqueta: 'Nombre', tipo: 'texto', requerido: true },
			{ nombre: 'descripcion', etiqueta: 'Descripcion', tipo: 'texto' },
			{ nombre: 'unidad_id', etiqueta: 'Unidad', tipo: 'relacion', tabla: 'unidades', mostrar: 'simbolo', requerido: true },
			{ nombre: 'tipo_nodo_id', etiqueta: 'Tipo de nodo', tipo: 'relacion', tabla: 'tipos_nodo', mostrar: 'nombre' },
			{ nombre: 'rango_min', etiqueta: 'Rango minimo', tipo: 'numero' },
			{ nombre: 'rango_max', etiqueta: 'Rango maximo', tipo: 'numero' }
		]
	},
	alias_variables: {
		ruta: 'alias-variables', modulo: 'alias-variables', titulo: 'Alias de variables', grupo: 'Catalogos',
		descripcion: 'Nombres con que los nodos reportan cada variable (sin cambiar codigo).',
		columnas: ['id', 'alias', 'variable_id', 'estado'],
		campos: [
			{ nombre: 'alias', etiqueta: 'Alias', tipo: 'texto', requerido: true },
			{ nombre: 'variable_id', etiqueta: 'Variable', tipo: 'relacion', tabla: 'variables', mostrar: 'codigo', requerido: true }
		]
	},
	sensores: {
		ruta: 'sensores', modulo: 'sensores', titulo: 'Sensores', grupo: 'Catalogos',
		descripcion: 'Sensores instalados en cada nodo.',
		columnas: ['id', 'nodo_id', 'variable_id', 'modelo', 'fecha_instalacion', 'estado'],
		campos: [
			{ nombre: 'nodo_id', etiqueta: 'Nodo', tipo: 'relacion', tabla: 'nodos', mostrar: 'codigo', requerido: true },
			{ nombre: 'variable_id', etiqueta: 'Variable', tipo: 'relacion', tabla: 'variables', mostrar: 'codigo', requerido: true },
			{ nombre: 'modelo', etiqueta: 'Modelo', tipo: 'texto', requerido: true },
			{ nombre: 'fecha_instalacion', etiqueta: 'Fecha de instalacion (AAAA-MM-DD)', tipo: 'texto' }
		]
	},
	umbrales: {
		ruta: 'umbrales', modulo: 'umbrales', titulo: 'Umbrales', grupo: 'Alertas',
		descripcion: 'Limites que disparan alertas de advertencia y criticas.',
		columnas: ['id', 'variable_id', 'nivel', 'minimo', 'maximo', 'mensaje', 'estado'],
		campos: [
			{ nombre: 'variable_id', etiqueta: 'Variable', tipo: 'relacion', tabla: 'variables', mostrar: 'codigo', requerido: true },
			{ nombre: 'nivel', etiqueta: 'Nivel', tipo: 'seleccion', opciones: ['ADVERTENCIA', 'CRITICO'], requerido: true },
			{ nombre: 'minimo', etiqueta: 'Minimo', tipo: 'numero', ayuda: 'Alerta si el valor es menor' },
			{ nombre: 'maximo', etiqueta: 'Maximo', tipo: 'numero', ayuda: 'Alerta si el valor es mayor' },
			{ nombre: 'mensaje', etiqueta: 'Mensaje', tipo: 'texto' }
		]
	},
	alertas: {
		ruta: 'alertas', modulo: 'alertas', titulo: 'Alertas', grupo: 'Alertas',
		descripcion: 'Alertas generadas por las mediciones. Marquelas como atendidas.',
		columnas: ['id', 'mensaje', 'atendida', 'creado', 'estado'],
		campos: [
			{ nombre: 'mensaje', etiqueta: 'Mensaje', tipo: 'texto' },
			{ nombre: 'atendida', etiqueta: 'Atendida', tipo: 'bool' }
		]
	},
	notificaciones: {
		ruta: 'notificaciones', modulo: 'notificaciones', titulo: 'Notificaciones', grupo: 'Alertas',
		descripcion: 'Bitacora de avisos enviados por correo.', soloLectura: true,
		columnas: ['id', 'alerta_id', 'usuario_id', 'canal', 'destino', 'situacion', 'detalle', 'creado'],
		campos: []
	},
	zonas_riego: {
		ruta: 'zonas-riego', modulo: 'zonas-riego', titulo: 'Zonas de riego', grupo: 'Riego',
		descripcion: 'Zonas regadas, sensor que decide y limites de seguridad.',
		columnas: ['id', 'codigo', 'nombre', 'modo', 'humedad_min', 'humedad_max', 'limite_diario_s', 'estado'],
		campos: [
			{ nombre: 'codigo', etiqueta: 'Codigo', tipo: 'texto', requerido: true },
			{ nombre: 'nombre', etiqueta: 'Nombre', tipo: 'texto', requerido: true },
			{ nombre: 'descripcion', etiqueta: 'Descripcion', tipo: 'texto' },
			{ nombre: 'ambito_id', etiqueta: 'Ambito', tipo: 'relacion', tabla: 'ambitos', mostrar: 'nombre', requerido: true },
			{ nombre: 'nodo_sensor_id', etiqueta: 'Nodo sensor', tipo: 'relacion', tabla: 'nodos', mostrar: 'codigo' },
			{ nombre: 'variable_id', etiqueta: 'Variable que decide', tipo: 'relacion', tabla: 'variables', mostrar: 'codigo' },
			{ nombre: 'humedad_min', etiqueta: 'Humedad minima (abre)', tipo: 'numero' },
			{ nombre: 'humedad_max', etiqueta: 'Humedad maxima (cierra)', tipo: 'numero' },
			{ nombre: 'duracion_max_s', etiqueta: 'Duracion maxima (s)', tipo: 'numero' },
			{ nombre: 'descanso_min_s', etiqueta: 'Descanso minimo (s)', tipo: 'numero' },
			{ nombre: 'limite_diario_s', etiqueta: 'Limite diario (s)', tipo: 'numero' }
		]
	},
	actuadores: {
		ruta: 'actuadores', modulo: 'actuadores', titulo: 'Actuadores', grupo: 'Riego',
		descripcion: 'Valvulas motorizadas y bomba.',
		columnas: ['id', 'codigo', 'nombre', 'tipo', 'zona_riego_id', 'posicion', 'ultimo_reporte', 'estado'],
		campos: [
			{ nombre: 'codigo', etiqueta: 'Codigo', tipo: 'texto', requerido: true },
			{ nombre: 'nombre', etiqueta: 'Nombre', tipo: 'texto', requerido: true },
			{ nombre: 'tipo', etiqueta: 'Tipo', tipo: 'seleccion', opciones: ['VALVULA', 'BOMBA'], requerido: true },
			{ nombre: 'zona_riego_id', etiqueta: 'Zona de riego', tipo: 'relacion', tabla: 'zonas_riego', mostrar: 'nombre' },
			{ nombre: 'hardware', etiqueta: 'Hardware', tipo: 'texto' }
		]
	},
	programas_riego: {
		ruta: 'programas-riego', modulo: 'programas-riego', titulo: 'Programas de riego', grupo: 'Riego',
		descripcion: 'Horarios de riego programado por zona.',
		columnas: ['id', 'zona_riego_id', 'hora_inicio', 'duracion_s', 'dias', 'habilitado', 'estado'],
		campos: [
			{ nombre: 'zona_riego_id', etiqueta: 'Zona', tipo: 'relacion', tabla: 'zonas_riego', mostrar: 'nombre', requerido: true },
			{ nombre: 'hora_inicio', etiqueta: 'Hora de inicio (HH:MM)', tipo: 'hora', requerido: true },
			{ nombre: 'duracion_s', etiqueta: 'Duracion (s)', tipo: 'numero', requerido: true },
			{ nombre: 'dias', etiqueta: 'Dias (L M X J V S D como 1111100)', tipo: 'texto', ayuda: '7 caracteres de 0 y 1' },
			{ nombre: 'habilitado', etiqueta: 'Habilitado', tipo: 'bool' }
		]
	},
	comandos_riego: {
		ruta: 'comandos-riego', modulo: 'comandos-riego', titulo: 'Ordenes de riego', grupo: 'Riego',
		descripcion: 'Cola de ordenes del panel al controlador.', soloLectura: true,
		columnas: ['id', 'actuador_id', 'accion', 'duracion_s', 'origen', 'situacion', 'detalle', 'creado'],
		campos: []
	},
	eventos_riego: {
		ruta: 'eventos-riego', modulo: 'eventos-riego', titulo: 'Bitacora de riego', grupo: 'Riego',
		descripcion: 'Riegos ejecutados, su duracion y su origen.', soloLectura: true,
		columnas: ['id', 'actuador_id', 'zona_riego_id', 'inicio', 'fin', 'duracion_s', 'origen', 'motivo'],
		campos: []
	}
};

/** Clave del catalogo a partir de la ruta de la URL ("tipos-nodo" -> "tipos_nodo"). */
export function claveDeTabla(segmento) {
	const clave = segmento.replaceAll('-', '_');
	return clave in TABLAS ? clave : null;
}

/** URL amigable de una tabla: /tipos-nodo */
export function urlDeTabla(clave) {
	return '/' + clave.replaceAll('_', '-');
}

export const GRUPOS = ['Seguridad', 'Infraestructura', 'Catalogos', 'Alertas', 'Riego'];
