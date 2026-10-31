<script>
	import { onMount } from 'svelte';
	import { api_historial } from '#lib/servicios/datos.js';
	import { TablaDatos, Input, Select, Button, Alert, Spinner } from '#lib';

	let filtros = $state({ ambito: '', nodo: '', variable: '', desde: '', hasta: '' });
	let datos = $state({ total: 0, datos: [] });
	let error = $state('');
	let cargando = $state(true);

	const columnas = [
		{ titulo: 'Fecha', campo: 'fecha_recepcion', tipo: 'fecha' },
		{ titulo: 'Nodo', campo: 'nodo' },
		{ titulo: 'Ambito', campo: 'ambito' },
		{ titulo: 'Variable', campo: 'variable_nombre' },
		{ titulo: 'Valor', campo: 'valor', formato: (v) => (v == null ? '' : Number(v).toFixed(2)) },
		{ titulo: 'Unidad', campo: 'unidad' },
		{ titulo: 'RSSI', campo: 'rssi' },
		{ titulo: 'SNR', campo: 'snr' }
	];

	async function buscar() {
		cargando = true;
		error = '';
		try {
			datos = await api_historial.listar({
				ambito: filtros.ambito,
				nodo: filtros.nodo.trim(),
				variable: filtros.variable.trim(),
				desde: filtros.desde ? new Date(filtros.desde).toISOString() : '',
				hasta: filtros.hasta ? new Date(filtros.hasta).toISOString() : ''
			});
		} catch (e) {
			error = e.message;
		} finally {
			cargando = false;
		}
	}

	function descargar() {
		const filas = datos.datos.map((f) => [f.fecha_recepcion, f.nodo, f.ambito, f.variable, f.valor, f.unidad, f.rssi, f.snr, f.latitud, f.longitud]);
		const texto = ['fecha,nodo,ambito,variable,valor,unidad,rssi,snr,latitud,longitud', ...filas.map((r) => r.map((x) => `"${String(x ?? '').replaceAll('"', '""')}"`).join(','))].join('\n');
		const url = URL.createObjectURL(new Blob([texto], { type: 'text/csv;charset=utf-8' }));
		const a = document.createElement('a');
		a.href = url;
		a.download = 'historial.csv';
		a.click();
		URL.revokeObjectURL(url);
	}

	onMount(buscar);
</script>

<svelte:head><title>Historial | IoT-Mangrove</title></svelte:head>

<div class="pagina">
	<h1>Historial</h1>
	<p class="muted">Mediciones guardadas. Filtre en el servidor y luego busque u ordene en la tabla.</p>

	<form class="barra" onsubmit={(e) => { e.preventDefault(); buscar(); }}>
		<Select label="Ambito" name="ambito" vacio="Todos" opciones={[{ valor: 'MANGLAR', texto: 'Manglar' }, { valor: 'VIVERO', texto: 'Vivero' }, { valor: 'RIEGO', texto: 'Riego' }]} bind:value={filtros.ambito} />
		<Input label="Nodo (ej. 0XAA)" name="nodo" bind:value={filtros.nodo} />
		<Input label="Variable (ej. ph)" name="variable" bind:value={filtros.variable} />
		<Input label="Desde" name="desde" type="datetime-local" bind:value={filtros.desde} />
		<Input label="Hasta" name="hasta" type="datetime-local" bind:value={filtros.hasta} />
		<Button type="submit">Buscar</Button>
		<Button variant="secondary" onclick={descargar} disabled={!datos.datos.length}>Descargar CSV</Button>
	</form>

	{#if error}<Alert tone="danger">{error}</Alert>{/if}
	{#if cargando}
		<Spinner />
	{:else}
		<p class="muted">{datos.total} registros en total{datos.total > datos.datos.length ? `; se muestran los ${datos.datos.length} mas recientes` : ''}.</p>
		<TablaDatos {columnas} filas={datos.datos} orden={[[0, 'desc']]} />
	{/if}
</div>
