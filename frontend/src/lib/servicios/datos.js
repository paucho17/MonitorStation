/** Consultas de datos y operaciones especiales (no son CRUD simple). */
import { solicitar } from './cliente.js';

export const api_dashboard = {
	/** @param {string} [ambito] MANGLAR, VIVERO, RIEGO o vacio para todos */
	obtener: (ambito) => solicitar('/api/dashboard', { params: { ambito } })
};

export const api_historial = {
	/** @param {{nodo?:string, variable?:string, ambito?:string, desde?:string, hasta?:string, limite?:number}} filtros */
	listar: (filtros) => solicitar('/api/historial', { params: { limite: 1000, ...filtros } })
};

export const api_riego = {
	estado: () => solicitar('/api/riego/estado'),
	/** @param {number} zonaId @param {'AUTO'|'PROGRAMADO'|'MANUAL'|'APAGADO'} modo */
	cambiarModo: (zonaId, modo) => solicitar(`/api/riego/zonas/${zonaId}/modo`, { metodo: 'PUT', cuerpo: { modo } }),
	/** @param {number} actuadorId @param {'ABRIR'|'CERRAR'} accion @param {number} [duracion_s] */
	ordenar: (actuadorId, accion, duracion_s) =>
		solicitar('/api/riego/comandos', { metodo: 'POST', cuerpo: { actuador_id: actuadorId, accion, duracion_s } })
};

export const api_notificaciones_usuario = {
	preferencias: () => solicitar('/api/notificaciones/preferencias'),
	/** @param {{notificar_alertas:boolean, notificar_nivel:string}} datos */
	guardar: (datos) => solicitar('/api/notificaciones/preferencias', { metodo: 'PUT', cuerpo: datos }),
	probar: () => solicitar('/api/notificaciones/prueba', { metodo: 'POST' })
};

export const api_registro = {
	/** @param {{username:string, password:string, email?:string, nombre_completo?:string}} datos */
	crear: (datos) => solicitar('/api/auth/registro', { metodo: 'POST', cuerpo: datos })
};

export const api_chatbot = {
	/** @param {string} q */
	preguntar: (q) => solicitar('/aux/chatbot/consultar', { metodo: 'POST', cuerpo: { q, origen: 'web' } })
};
