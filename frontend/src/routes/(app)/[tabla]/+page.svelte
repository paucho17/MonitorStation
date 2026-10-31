<!--
	Lista generica de una tabla (equivale a /estudiantes/+page.svelte del curso):
	la ruta /[tabla] sirve cualquier entrada del catalogo TABLAS segun los permisos del rol.
-->
<script>
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { sesion } from '#lib/estado/sesion.svelte.js';
	import { SERVICIOS, TABLAS, claveDeTabla, urlDeTabla } from '#lib/servicios/index.js';
	import { solicitar } from '#lib/servicios/cliente.js';
	import { TablaDatos, Button, Alert, Spinner, Checkbox, Modal } from '#lib';

	const clave = $derived(claveDeTabla(page.params.tabla));
	const tabla = $derived(clave ? TABLAS[clave] : null);

	let filas = $state([]);
	let relaciones = $state({});
	let cargando = $state(true);
	let error = $state('');
	let aviso = $state('');
	let verEliminados = $state(false);
	let claveNueva = $state(null);

	const puede = (accion) => !!tabla && sesion.puede(tabla.modulo, accion);

	const FECHAS = ['creado', 'actualizado', 'ultima_conexion', 'ultimo_reporte', 'inicio', 'fin', 'fecha_instalacion', 'fecha_recepcion'];

	const columnas = $derived.by(() => {
		if (!tabla) return [];
		return tabla.columnas.map((nombre) => {
			const campo = tabla.campos.find((c) => c.nombre === nombre);
			const titulo = campo?.etiqueta ?? nombre.replaceAll('_', ' ');
			if (campo?.tipo === 'relacion') {
				const mapa = new Map((relaciones[campo.tabla] ?? []).map((f) => [f.id, f[campo.mostrar]]));
				return { titulo, campo: nombre, formato: (v) => (v == null ? '' : (mapa.get(v) ?? v)) };
			}
			if (nombre.endsWith('_id')) return { titulo: titulo.replace(/ id$/, ''), campo: nombre };
			if (['estado', 'atendida', 'habilitado'].includes(nombre) || campo?.tipo === 'bool' || nombre.startsWith('notificar_')) return { titulo, campo: nombre, tipo: 'bool' };
			if (FECHAS.includes(nombre)) return { titulo, campo: nombre, tipo: 'fecha' };
			return { titulo, campo: nombre };
		});
	});

	const acciones = $derived.by(() => {
		if (!tabla || tabla.soloLectura) return tabla && clave === 'gateways' ? [] : [];
		const lista = [];
		if (puede('editar')) lista.push({ id: 'editar', texto: 'Editar', visible: (f) => f.estado !== false });
		if (clave === 'gateways' && puede('editar')) lista.push({ id: 'rotar', texto: 'Rotar clave', visible: (f) => f.estado !== false });
		if (puede('eliminar')) {
			lista.push({ id: 'eliminar', texto: 'Eliminar', clase: 'peligro', visible: (f) => f.estado !== false });
			lista.push({ id: 'restaurar', texto: 'Restaurar', visible: (f) => f.estado === false });
		}
		// Tablas de solo lectura con eliminacion logica
		return lista;
	});

	async function cargar() {
		if (!tabla) return;
		cargando = true;
		error = '';
		try {
			const servicio = SERVICIOS[clave];
			const peticiones = [servicio.listar({ incluir_inactivos: verEliminados || undefined })];
			// Tablas relacionadas para mostrar nombres en lugar de numeros
			const dependencias = [...new Set(tabla.campos.filter((c) => c.tipo === 'relacion').map((c) => c.tabla))];
			const visibles = dependencias.filter((d) => TABLAS[d] && sesion.puede(TABLAS[d].modulo));
			peticiones.push(...visibles.map((d) => SERVICIOS[d].listar()));
			const resultados = await Promise.all(peticiones);
			filas = resultados[0].datos;
			relaciones = Object.fromEntries(visibles.map((d, i) => [d, resultados[i + 1].datos]));
		} catch (e) {
			error = e.message;
		} finally {
			cargando = false;
		}
	}

	async function accion(id, fila) {
		error = aviso = '';
		try {
			if (id === 'editar') return goto(`${urlDeTabla(clave)}/${fila.id}`);
			if (id === 'eliminar') {
				if (!confirm(`Eliminar el registro ${fila.id}? Es una eliminacion logica y se puede restaurar.`)) return;
				await SERVICIOS[clave].eliminar(fila.id);
				aviso = `Registro ${fila.id} eliminado`;
			}
			if (id === 'restaurar') {
				await SERVICIOS[clave].restaurar(fila.id);
				aviso = `Registro ${fila.id} restaurado`;
			}
			if (id === 'rotar') {
				if (!confirm('La clave anterior dejara de funcionar. ¿Generar una nueva?')) return;
				claveNueva = await solicitar(`/api/gateways/${fila.id}/rotar-clave`, { metodo: 'POST' });
			}
			await cargar();
		} catch (e) {
			error = e.message;
		}
	}

	// Recarga al cambiar de tabla o de filtro
	$effect(() => {
		clave;
		verEliminados;
		cargar();
	});
</script>

<svelte:head><title>{tabla?.titulo ?? 'No encontrado'} | IoT-Mangrove</title></svelte:head>

<div class="pagina">
	{#if !tabla}
		<Alert tone="warning" title="Pagina no encontrada">No existe la tabla "{page.params.tabla}".</Alert>
	{:else if !puede('leer')}
		<Alert tone="warning" title="Sin acceso">Su rol no tiene permiso para ver {tabla.titulo}.</Alert>
	{:else}
		<div class="barra">
			<div class="crece"><h1>{tabla.titulo}</h1><p class="muted">{tabla.descripcion}</p></div>
			{#if puede('eliminar') && !tabla.soloLectura}<Checkbox label="Ver eliminados" bind:checked={verEliminados} />{/if}
			{#if puede('crear') && !tabla.soloLectura}<Button href={`${urlDeTabla(clave)}/nuevo`}>Nuevo</Button>{/if}
		</div>
		{#if aviso}<Alert tone="success" dismissible>{aviso}</Alert>{/if}
		{#if error}<Alert tone="danger">{error}</Alert>{/if}
		{#if cargando}
			<Spinner />
		{:else}
			<TablaDatos {columnas} {filas} {acciones} onaccion={accion} />
		{/if}
	{/if}
</div>

<Modal title="Clave de API del gateway" open={!!claveNueva} onclose={() => (claveNueva = null)}>
	{#if claveNueva}
		<Alert tone="warning">Guarde esta clave ahora: no se volvera a mostrar.</Alert>
		<p>Gateway <strong>{claveNueva.codigo}</strong></p>
		<code class="clave">{claveNueva.api_key}</code>
		<p><Button onclick={() => (claveNueva = null)}>Ya la guarde</Button></p>
	{/if}
</Modal>

<style>
	.clave {
		display: block;
		padding: 0.6rem;
		background: var(--color-bg);
		border-radius: var(--radius);
		word-break: break-all;
	}
</style>
