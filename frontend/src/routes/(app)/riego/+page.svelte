<script>
	import { onMount } from 'svelte';
	import { api_riego } from '#lib/servicios/datos.js';
	import { sesion } from '#lib/estado/sesion.svelte.js';
	import { Grid, Card, Badge, Button, Select, Input, Alert, Spinner, Section, TablaDatos } from '#lib';

	let estado = $state(null);
	let error = $state('');
	let aviso = $state('');
	let cargando = $state(true);
	let duraciones = $state({});

	const puedeEditar = $derived(sesion.puede('riego', 'editar'));
	const puedeOrdenar = $derived(sesion.puede('riego', 'crear'));
	const MODOS = ['AUTO', 'PROGRAMADO', 'MANUAL', 'APAGADO'];

	const columnasEventos = [
		{ titulo: 'Inicio', campo: 'inicio', tipo: 'fecha' },
		{ titulo: 'Actuador', campo: 'actuador' },
		{ titulo: 'Zona', campo: 'zona' },
		{ titulo: 'Duracion (s)', campo: 'duracion_s' },
		{ titulo: 'Origen', campo: 'origen' },
		{ titulo: 'Motivo', campo: 'motivo' }
	];

	async function cargar() {
		try {
			estado = await api_riego.estado();
			error = '';
		} catch (e) {
			error = e.message;
		} finally {
			cargando = false;
		}
	}

	async function modo(zona, nuevo) {
		try {
			await api_riego.cambiarModo(zona.id, nuevo);
			aviso = `Zona ${zona.codigo}: modo ${nuevo}`;
			await cargar();
		} catch (e) {
			error = e.message;
		}
	}

	async function ordenar(zona, actuador, accion) {
		try {
			const dur = Number(duraciones[actuador.id]);
			const r = await api_riego.ordenar(actuador.id, accion, accion === 'ABRIR' && dur > 0 ? dur : undefined);
			aviso = `Orden ${accion} enviada a ${actuador.codigo} (${r.situacion ?? 'PENDIENTE'})`;
			await cargar();
		} catch (e) {
			error = e.message;
		}
	}

	onMount(() => {
		cargar();
		const t = setInterval(cargar, 10000);
		return () => clearInterval(t);
	});
</script>

<svelte:head><title>Riego | IoT-Mangrove</title></svelte:head>

<div class="pagina">
	<h1>Riego</h1>
	<p class="muted">Estado de las zonas, modo de operacion y mando manual. Las ordenes pasan por la API, que aplica los limites de seguridad.</p>

	{#if aviso}<Alert tone="success" dismissible>{aviso}</Alert>{/if}
	{#if error}<Alert tone="danger" dismissible>{error}</Alert>{/if}

	{#if cargando}
		<Spinner />
	{:else if estado}
		<p class="muted">Ordenes en curso: <Badge tone={estado.comandos_en_curso ? 'warning' : 'neutral'}>{estado.comandos_en_curso}</Badge></p>
		<Grid min="22rem">
			{#each estado.zonas as z (z.id)}
				<Card title={`${z.nombre} (${z.codigo})`}>
					<p>
						Humedad:
						<strong>{z.humedad_actual != null ? Number(z.humedad_actual).toFixed(1) + ' %' : 'sin dato'}</strong>
						<span class="muted"> · abre bajo {z.humedad_min ?? '-'} %, cierra sobre {z.humedad_max ?? '-'} %</span>
					</p>
					<p class="muted">Hoy: {z.regado_hoy_s} s de {z.limite_diario_s ?? '-'} s permitidos</p>
					<Select label="Modo" name={`modo-${z.id}`} vacio={null} opciones={MODOS.map((m) => ({ valor: m, texto: m }))} value={z.modo} onchange={(e) => modo(z, e.currentTarget.value)} />
					{#if !puedeEditar}<small class="muted">Solo lectura</small>{/if}
					{#each z.actuadores as a (a.id)}
						<div class="actuador">
							<span><strong>{a.nombre}</strong> <Badge tone={a.posicion === 'ABIERTA' ? 'success' : 'neutral'}>{a.posicion ?? 'desconocida'}</Badge></span>
							{#if puedeOrdenar && z.modo === 'MANUAL'}
								<Input label="Duracion (s)" name={`dur-${a.id}`} type="number" bind:value={duraciones[a.id]} />
								<div class="fila">
									<Button size="sm" onclick={() => ordenar(z, a, 'ABRIR')}>Abrir</Button>
									<Button size="sm" variant="secondary" onclick={() => ordenar(z, a, 'CERRAR')}>Cerrar</Button>
								</div>
							{:else if puedeOrdenar}
								<small class="muted">Cambie a modo MANUAL para ordenar abrir o cerrar.</small>
							{/if}
						</div>
					{/each}
				</Card>
			{:else}
				<p class="muted">No hay zonas de riego configuradas.</p>
			{/each}
		</Grid>

		<Section title="Ultimos riegos">
			<TablaDatos columnas={columnasEventos} filas={estado.ultimos_eventos} orden={[[0, 'desc']]} />
		</Section>
	{/if}
</div>

<style>
	.actuador {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		margin-top: 0.75rem;
		padding-top: 0.75rem;
		border-top: 1px dashed var(--color-border);
	}
	.fila {
		display: flex;
		gap: 0.5rem;
	}
</style>
