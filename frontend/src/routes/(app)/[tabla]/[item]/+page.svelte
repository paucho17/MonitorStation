<!--
	Formulario de un registro: crea (/tabla/nuevo) o edita (/tabla/<id>).
-->
<script>
	import { getContext } from 'svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { SERVICIOS, urlDeTabla } from '#lib/servicios/index.js';
	import { sesion } from '#lib/estado/sesion.svelte.js';
	import { FormularioCrud, Alert, Modal, Button } from '#lib';

	const ctx = getContext('registro');
	const tabla = ctx.tabla;
	const clave = ctx.clave;
	const creando = ctx.creando;
	const lista = urlDeTabla(clave);

	const permitido = tabla && !tabla.soloLectura && sesion.puede(tabla.modulo, creando ? 'crear' : 'editar');

	// Valores iniciales: el registro existente o los valores por defecto
	function inicial() {
		const v = {};
		for (const c of tabla?.campos ?? []) {
			const actual = ctx.registro?.[c.nombre];
			if (c.tipo === 'bool') v[c.nombre] = actual ?? (creando && c.nombre.startsWith('puede_') ? false : !!actual);
			else if (c.tipo === 'hora') v[c.nombre] = actual ? String(actual).slice(0, 5) : '';
			else v[c.nombre] = actual ?? '';
		}
		return v;
	}
	let valores = $state(inicial());
	let error = $state('');
	let enviando = $state(false);
	let claveNueva = $state(null);

	/** Convierte el formulario en el cuerpo JSON de la API (vacios fuera, numeros reales). */
	function cuerpo() {
		const salida = {};
		for (const c of tabla.campos) {
			if (!creando && c.soloCrear) continue;
			let v = valores[c.nombre];
			if (c.tipo === 'bool') {
				salida[c.nombre] = !!v;
				continue;
			}
			if (v === '' || v === null || v === undefined) {
				// En edicion, un campo opcional vaciado se envia como null; en creacion se omite
				if (!creando && c.tipo !== 'clave' && !c.requerido) salida[c.nombre] = null;
				continue;
			}
			if (c.tipo === 'numero' || c.tipo === 'relacion') v = Number(v);
			if (c.tipo === 'hora') v = String(v).length === 5 ? v + ':00' : v;
			salida[c.nombre] = v;
		}
		return salida;
	}

	async function guardar() {
		error = '';
		enviando = true;
		try {
			if (creando) {
				const r = await SERVICIOS[clave].crear(cuerpo());
				if (clave === 'gateways' && r.api_key) {
					claveNueva = r;
					return;
				}
			} else {
				await SERVICIOS[clave].actualizar(page.params.item, cuerpo());
			}
			await goto(lista);
		} catch (e) {
			error = e.message;
		} finally {
			enviando = false;
		}
	}
</script>

<svelte:head><title>{creando ? 'Nuevo' : 'Editar'} {tabla?.titulo} | IoT-Mangrove</title></svelte:head>

<div class="pagina">
	<p><a href={lista}>← {tabla?.titulo}</a></p>
	<h1>{creando ? 'Nuevo registro' : `Editar registro ${page.params.item}`}</h1>
	{#if !tabla}
		<Alert tone="warning">Tabla no encontrada.</Alert>
	{:else if !permitido}
		<Alert tone="warning" title="Sin acceso">Su rol no puede {creando ? 'crear' : 'editar'} en {tabla.titulo}.</Alert>
	{:else}
		<FormularioCrud {tabla} bind:valores relaciones={ctx.relaciones} {creando} {enviando} {error} onguardar={guardar} oncancelar={() => goto(lista)} />
	{/if}
</div>

<Modal title="Clave de API del gateway" open={!!claveNueva} onclose={() => goto(lista)}>
	{#if claveNueva}
		<Alert tone="warning">Guarde esta clave ahora: no se volvera a mostrar.</Alert>
		<p>Gateway <strong>{claveNueva.codigo}</strong></p>
		<code>{claveNueva.api_key}</code>
		<p><Button onclick={() => goto(lista)}>Ya la guarde</Button></p>
	{/if}
</Modal>
