<script>
	import { onMount } from 'svelte';
	import { api_dashboard } from '#lib/servicios/datos.js';
	import { sesion } from '#lib/estado/sesion.svelte.js';
	import { Section, Grid, Medidor, Tabs, Alert, Badge, Spinner, Card } from '#lib';

	const AMBITOS = [
		{ valor: '', texto: 'Todos' },
		{ valor: 'MANGLAR', texto: 'Manglar' },
		{ valor: 'VIVERO', texto: 'Vivero' },
		{ valor: 'RIEGO', texto: 'Riego' }
	];

	let ambito = $state('');
	let datos = $state(null);
	let error = $state('');
	let cargando = $state(true);

	async function cargar() {
		try {
			datos = await api_dashboard.obtener(ambito);
			error = '';
		} catch (e) {
			error = e.message;
		} finally {
			cargando = false;
		}
	}

	onMount(() => {
		cargar();
		const t = setInterval(cargar, 15000);
		return () => clearInterval(t);
	});

	// Agrupa las variables por nodo para leerlas por estacion
	const porNodo = $derived.by(() => {
		const m = new Map();
		for (const v of datos?.variables ?? []) {
			if (!m.has(v.nodo)) m.set(v.nodo, { nodo: v.nodo, nombre: v.nodo_nombre, ambito: v.ambito, variables: [] });
			m.get(v.nodo).variables.push(v);
		}
		return [...m.values()];
	});

	const posicion = $derived(datos?.ultima_posicion);
	const hora = (f) => (f ? new Date(f).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'medium' }) : 'sin datos');
</script>

<svelte:head><title>Panel | IoT-Mangrove</title></svelte:head>

<div class="pagina">
	<div class="barra">
		<div class="crece"><h1>Panel</h1><p class="muted">Ultimo valor recibido de cada variable. Se actualiza cada 15 segundos.</p></div>
		<Tabs opciones={AMBITOS} bind:value={ambito} onchange={cargar} />
	</div>

	{#if error}<Alert tone="danger">{error}</Alert>{/if}
	{#if cargando}
		<Spinner />
	{:else if datos}
		<Grid min="14rem">
			<Card title="Ultima lectura">
				{#if datos.ultima_lectura}
					Nodo <strong>{datos.ultima_lectura.nodo}</strong> via {datos.ultima_lectura.gateway}<br />
					<small class="muted">{hora(datos.ultima_lectura.fecha_recepcion)} · RSSI {datos.ultima_lectura.rssi ?? '-'} dBm · SNR {datos.ultima_lectura.snr ?? '-'}</small>
				{:else}Sin lecturas{/if}
			</Card>
			<Card title="Alertas pendientes">
				<span class="grande">{datos.alertas_pendientes}</span>
				{#if sesion.puede('alertas')}
					{#snippet footer()}<a href="/alertas">Ver alertas</a>{/snippet}
				{/if}
			</Card>
			<Card title="Ultima posicion GPS">
				{#if posicion}
					<a href={`https://www.openstreetmap.org/?mlat=${posicion.latitud}&mlon=${posicion.longitud}#map=16/${posicion.latitud}/${posicion.longitud}`} target="_blank" rel="noopener noreferrer">
						{Number(posicion.latitud).toFixed(5)}, {Number(posicion.longitud).toFixed(5)}
					</a><br />
					<small class="muted">Nodo {posicion.nodo} · {posicion.satelites ?? '-'} satelites</small>
				{:else}Sin posicion{/if}
			</Card>
		</Grid>

		{#each porNodo as n (n.nodo)}
			<Section title={`Nodo ${n.nodo}`} description={`${n.nombre ?? ''} · ${n.ambito}`}>
				<Grid min="13rem">
					{#each n.variables as v (v.variable)}
						<Medidor nombre={v.variable_nombre} valor={v.valor} unidad={v.unidad} nivel={v.alerta_nivel} nodo={v.nodo} fecha={v.fecha_recepcion} />
					{/each}
				</Grid>
			</Section>
		{:else}
			<p class="muted">Aun no hay datos para este ambito.</p>
		{/each}
	{/if}
</div>

<style>
	.grande {
		font-size: 2.4rem;
		font-weight: 700;
	}
</style>
