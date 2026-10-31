/**
 * Cliente HTTP de la API de IoT-Mangrove.
 *
 * Agrega la cabecera Authorization con el JWT de la sesion y convierte los
 * errores de la API en excepciones con un mensaje legible. Si el servidor
 * responde 401 (token vencido o revocado) cierra la sesion local.
 */
import { sesion } from '#lib/estado/sesion.svelte.js';

export class ErrorApi extends Error {
	/** @param {string} mensaje @param {number} estado */
	constructor(mensaje, estado) {
		super(mensaje);
		this.estado = estado;
	}
}

/** Extrae un texto util del cuerpo de error de FastAPI o Express. */
function mensajeDe(cuerpo, estado) {
	if (!cuerpo) return `Error ${estado}`;
	const d = cuerpo.detail ?? cuerpo.error ?? cuerpo.message;
	if (typeof d === 'string') return d;
	if (Array.isArray(d)) return d.map((e) => `${(e.loc ?? []).slice(1).join('.')}: ${e.msg}`).join('; ');
	return `Error ${estado}`;
}

/**
 * @param {string} ruta Ruta absoluta, p. ej. /api/dashboard
 * @param {{metodo?: string, cuerpo?: unknown, params?: Record<string, unknown>, base?: string}} [opciones]
 */
export async function solicitar(ruta, opciones = {}) {
	const { metodo = 'GET', cuerpo, params } = opciones;
	let url = ruta;
	if (params) {
		const q = new URLSearchParams();
		for (const [k, v] of Object.entries(params)) {
			if (v !== undefined && v !== null && v !== '') q.set(k, String(v));
		}
		const texto = q.toString();
		if (texto) url += (url.includes('?') ? '&' : '?') + texto;
	}
	/** @type {Record<string, string>} */
	const cabeceras = {};
	if (cuerpo !== undefined) cabeceras['Content-Type'] = 'application/json';
	if (sesion.token) cabeceras.Authorization = `Bearer ${sesion.token}`;

	let respuesta;
	try {
		respuesta = await fetch(url, {
			method: metodo,
			headers: cabeceras,
			body: cuerpo !== undefined ? JSON.stringify(cuerpo) : undefined
		});
	} catch {
		throw new ErrorApi('No hay conexion con el servidor', 0);
	}
	let datos = null;
	try {
		datos = await respuesta.json();
	} catch {
		/* respuesta sin cuerpo */
	}
	if (!respuesta.ok) {
		if (respuesta.status === 401 && sesion.token) sesion.cerrarLocal();
		throw new ErrorApi(mensajeDe(datos, respuesta.status), respuesta.status);
	}
	return datos;
}

/**
 * Crea el servicio CRUD de un recurso de la API principal.
 * Todos los recursos comparten operaciones y eliminacion logica.
 * @param {string} ruta Nombre del recurso, p. ej. "usuarios"
 */
export function crearServicio(ruta) {
	const base = `/api/${ruta}`;
	return {
		ruta,
		/** @param {Record<string, unknown>} [filtros] */
		listar: (filtros = {}) => solicitar(base, { params: { limite: 500, ...filtros } }),
		/** @param {number|string} id */
		obtener: (id) => solicitar(`${base}/${id}`),
		/** @param {object} datos */
		crear: (datos) => solicitar(base, { metodo: 'POST', cuerpo: datos }),
		/** @param {number|string} id @param {object} datos */
		actualizar: (id, datos) => solicitar(`${base}/${id}`, { metodo: 'PUT', cuerpo: datos }),
		/** @param {number|string} id */
		eliminar: (id) => solicitar(`${base}/${id}`, { metodo: 'DELETE' }),
		/** @param {number|string} id */
		restaurar: (id) => solicitar(`${base}/${id}/restaurar`, { metodo: 'POST' })
	};
}
