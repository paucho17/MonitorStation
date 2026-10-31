/**
 * Estado de la sesion: JWT, usuario y permisos por modulo.
 *
 * El token vive en sessionStorage (se borra al cerrar la pestana). Los
 * permisos se piden a /api/auth/me y gobiernan que menus y botones se ven;
 * la API vuelve a validarlos en cada peticion, asi que ocultar un boton es
 * solo comodidad, nunca la seguridad.
 */

const CLAVE = 'iotmangrove.token';

function leer() {
	try {
		return sessionStorage.getItem(CLAVE) ?? '';
	} catch {
		return '';
	}
}

function guardar(valor) {
	try {
		if (valor) sessionStorage.setItem(CLAVE, valor);
		else sessionStorage.removeItem(CLAVE);
	} catch {
		/* almacenamiento no disponible: la sesion dura mientras la pagina */
	}
}

class Sesion {
	token = $state(leer());
	usuario = $state(/** @type {null | {id:number, username:string, email:string|null, rol:string}} */ (null));
	permisos = $state(/** @type {{modulo:string, puede_leer:boolean, puede_crear:boolean, puede_editar:boolean, puede_eliminar:boolean}[]} */ ([]));
	cargando = $state(false);

	get activa() {
		return !!this.token;
	}

	/** @param {string} modulo @param {'leer'|'crear'|'editar'|'eliminar'} [accion] */
	puede(modulo, accion = 'leer') {
		const p = this.permisos.find((x) => x.modulo === modulo);
		return !!p && !!p[`puede_${accion}`];
	}

	/** @param {string} username @param {string} password */
	async iniciar(username, password) {
		const r = await fetch('/api/auth/login', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ username, password })
		});
		const datos = await r.json().catch(() => null);
		if (!r.ok) {
			const detalle = datos?.detail;
			throw new Error(typeof detalle === 'string' ? detalle : 'No fue posible iniciar sesion');
		}
		this.token = datos.access_token;
		guardar(this.token);
		await this.cargarPerfil();
	}

	/** Recupera usuario y permisos con el token vigente. */
	async cargarPerfil() {
		if (!this.token) return;
		this.cargando = true;
		try {
			const r = await fetch('/api/auth/me', { headers: { Authorization: `Bearer ${this.token}` } });
			if (!r.ok) throw new Error('sesion invalida');
			const p = await r.json();
			this.usuario = { id: p.id, username: p.username, email: p.email, rol: p.rol };
			this.permisos = p.permisos;
		} catch {
			this.cerrarLocal();
		} finally {
			this.cargando = false;
		}
	}

	/** Cierra la sesion en el servidor (revoca el JWT) y en el navegador. */
	async cerrar() {
		if (this.token) {
			try {
				await fetch('/api/auth/logout', { method: 'POST', headers: { Authorization: `Bearer ${this.token}` } });
			} catch {
				/* sin conexion: igual se cierra localmente */
			}
		}
		this.cerrarLocal();
	}

	cerrarLocal() {
		this.token = '';
		this.usuario = null;
		this.permisos = [];
		guardar('');
	}
}

export const sesion = new Sesion();
