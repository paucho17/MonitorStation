<!--
	Layout de un registro (equivale a /[tabla]/[item]/+layout.svelte del curso):
	carga el registro y las tablas relacionadas una sola vez y las comparte con la pagina.
-->
<script>
	import { page } from '$app/state';
	import { setContext } from 'svelte';
	import { SERVICIOS, TABLAS, claveDeTabla } from '#lib/servicios/index.js';
	import { sesion } from '#lib/estado/sesion.svelte.js';
	import { Spinner, Alert } from '#lib';

	let { children } = $props();

	const clave = $derived(claveDeTabla(page.params.tabla));
	const tabla = $derived(clave ? TABLAS[clave] : null);
	const creando = $derived(page.params.item === 'nuevo');

	const contexto = $state({ cargando: true, error: '', registro: null, relaciones: {}, clave: null, tabla: null, creando: false });
	setContext('registro', contexto);

	async function cargar() {
		contexto.cargando = true;
		contexto.error = '';
		contexto.clave = clave;
		contexto.tabla = tabla;
		contexto.creando = creando;
		if (!tabla) {
			contexto.cargando = false;
			return;
		}
		try {
			const deps = [...new Set(tabla.campos.filter((c) => c.tipo === 'relacion').map((c) => c.tabla))].filter(
				(d) => TABLAS[d] && sesion.puede(TABLAS[d].modulo)
			);
			const [registro, ...filas] = await Promise.all([
				creando ? Promise.resolve(null) : SERVICIOS[clave].obtener(page.params.item),
				...deps.map((d) => SERVICIOS[d].listar())
			]);
			contexto.registro = registro;
			contexto.relaciones = Object.fromEntries(deps.map((d, i) => [d, filas[i].datos]));
		} catch (e) {
			contexto.error = e.message;
		} finally {
			contexto.cargando = false;
		}
	}

	$effect(() => {
		clave;
		page.params.item;
		cargar();
	});
</script>

{#if contexto.cargando}
	<div class="pagina"><Spinner /></div>
{:else if contexto.error}
	<div class="pagina"><Alert tone="danger">{contexto.error}</Alert></div>
{:else}
	{@render children()}
{/if}
