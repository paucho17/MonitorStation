<script>
	import { sesion } from '#lib/estado/sesion.svelte.js';
	import { TABLAS, GRUPOS, urlDeTabla } from '#lib/servicios/tablas.js';
	import { Section, Grid, Card, Badge } from '#lib';

	const grupos = $derived(
		GRUPOS.map((g) => ({
			titulo: g,
			tablas: Object.entries(TABLAS).filter(([, t]) => t.grupo === g && sesion.puede(t.modulo))
		})).filter((g) => g.tablas.length)
	);
</script>

<svelte:head><title>Administracion | IoT-Mangrove</title></svelte:head>

<div class="pagina">
	<h1>Administracion</h1>
	<p class="muted">Tablas del sistema a las que su rol tiene acceso. Cada una ofrece listar, crear, editar y eliminar (logico) segun sus permisos.</p>
	{#each grupos as g (g.titulo)}
		<Section title={g.titulo}>
			<Grid min="16rem">
				{#each g.tablas as [clave, t] (clave)}
					<Card title={t.titulo}>
						{t.descripcion}
						{#snippet footer()}
							<a href={urlDeTabla(clave)}>Abrir</a>
							{#if t.soloLectura}<Badge>solo lectura</Badge>{/if}
						{/snippet}
					</Card>
				{/each}
			</Grid>
		</Section>
	{/each}
</div>
