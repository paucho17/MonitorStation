<script>
	import { onMount } from 'svelte';
	import { api_alertas } from '#lib/servicios/api_alertas.js';
	import { sesion } from '#lib/estado/sesion.svelte.js';
	import { TablaDatos, Tabs, Alert, Spinner, Badge } from '#lib';

	let vista = $state('pendientes');
	let filas = $state([]);
	let error = $state('');
	let cargando = $state(true);
	let aviso = $state('');

	const columnas = [
		{ titulo: 'ID', campo: 'id' },
		{ titulo: 'Fecha', campo: 'creado', tipo: 'fecha' },
		{ titulo: 'Alerta', campo: 'mensaje' },
		{ titulo: 'Atendida', campo: 'atendida', tipo: 'bool' }
	];

	const acciones = $derived(
		sesion.puede('alertas', 'editar')
			? [
					{ id: 'atender', texto: 'Marcar atendida', visible: (f) => !f.atendida },
					{ id: 'reabrir', texto: 'Reabrir', visible: (f) => f.atendida }
				]
			: []
	);

	const visibles = $derived(
		filas.filter((f) => (vista === 'pendientes' ? !f.atendida : vista === 'atendidas' ? f.atendida : true))
	);

	async function cargar() {
		cargando = true;
		try {
			filas = (await api_alertas.listar()).datos;
			error = '';
		} catch (e) {
			error = e.message;
		} finally {
			cargando = false;
		}
	}

	async function accion(id, fila) {
		try {
			await api_alertas.actualizar(fila.id, { atendida: id === 'atender' });
			aviso = id === 'atender' ? `Alerta ${fila.id} atendida` : `Alerta ${fila.id} reabierta`;
			await cargar();
		} catch (e) {
			error = e.message;
		}
	}

	onMount(cargar);
</script>

<svelte:head><title>Alertas | IoT-Mangrove</title></svelte:head>

<div class="pagina">
	<div class="barra">
		<div class="crece"><h1>Alertas</h1><p class="muted">Valores fuera de umbral. Las criticas llegan ademas por correo si activo los avisos en su perfil.</p></div>
		<Tabs opciones={[{ valor: 'pendientes', texto: 'Pendientes' }, { valor: 'atendidas', texto: 'Atendidas' }, { valor: 'todas', texto: 'Todas' }]} bind:value={vista} />
	</div>
	{#if aviso}<Alert tone="success" dismissible>{aviso}</Alert>{/if}
	{#if error}<Alert tone="danger">{error}</Alert>{/if}
	{#if cargando}
		<Spinner />
	{:else}
		<p class="muted">{visibles.length} alertas <Badge tone={filas.some((f) => !f.atendida) ? 'warning' : 'success'}>{filas.filter((f) => !f.atendida).length} pendientes</Badge></p>
		<TablaDatos {columnas} filas={visibles} {acciones} onaccion={accion} />
	{/if}
</div>
