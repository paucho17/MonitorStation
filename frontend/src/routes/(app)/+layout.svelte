<script>
	import { goto } from '$app/navigation';
	import { sesion } from '#lib/estado/sesion.svelte.js';
	import { TABLAS, GRUPOS, urlDeTabla } from '#lib/servicios/tablas.js';
	import { Sidebar, Chatbot, Footer, Spinner, Badge, Button } from '#lib';

	let { children } = $props();
	let menuAbierto = $state(false);

	// Proteccion de rutas: sin token no hay panel
	$effect(() => {
		if (!sesion.activa) goto('/login');
	});

	// Paginas propias con su propio acceso; el resto sale del catalogo de tablas
	const PROPIAS = ['alertas'];

	const grupos = $derived.by(() => {
		const principal = [];
		if (sesion.puede('dashboard')) principal.push({ href: '/', texto: 'Panel' });
		if (sesion.puede('historial')) principal.push({ href: '/historial', texto: 'Historial' });
		if (sesion.puede('alertas')) principal.push({ href: '/alertas', texto: 'Alertas' });
		if (sesion.puede('riego')) principal.push({ href: '/riego', texto: 'Riego' });
		principal.push({ href: '/perfil', texto: 'Mi perfil' });
		const lista = [{ titulo: 'Principal', enlaces: principal }];
		for (const g of GRUPOS) {
			const enlaces = Object.entries(TABLAS)
				.filter(([clave, t]) => t.grupo === g && !PROPIAS.includes(clave) && sesion.puede(t.modulo))
				.map(([clave, t]) => ({ href: urlDeTabla(clave), texto: t.titulo }));
			if (enlaces.length) lista.push({ titulo: g, enlaces });
		}
		return lista;
	});

	async function salir() {
		await sesion.cerrar();
		await goto('/login');
	}
</script>

{#if !sesion.activa || !sesion.usuario}
	<div class="espera"><Spinner texto="Verificando sesion..." /></div>
{:else}
	<div class="app">
		<header class="barra-superior">
			<button class="hamburguesa" aria-label="Abrir menu" onclick={() => (menuAbierto = !menuAbierto)}>☰</button>
			<a class="marca" href="/">IoT-Mangrove</a>
			<span class="crece"></span>
			<span class="usuario">
				{sesion.usuario.username}
				<Badge tone="info">{sesion.usuario.rol}</Badge>
			</span>
			<Button size="sm" variant="secondary" onclick={salir}>Salir</Button>
		</header>
		<Sidebar {grupos} bind:open={menuAbierto} />
		<main>
			{@render children()}
			<Footer text="IoT-Mangrove, Universidad IUB. Barranquilla, Colombia." />
		</main>
		<Chatbot />
	</div>
{/if}

<style>
	.espera {
		min-height: 100vh;
		display: grid;
		place-items: center;
	}
	.app {
		display: grid;
		grid-template-columns: 15rem minmax(0, 1fr);
		grid-template-rows: auto 1fr;
		min-height: 100vh;
	}
	.barra-superior {
		grid-column: 1 / -1;
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.6rem 1rem;
		background: var(--color-surface);
		border-bottom: 1px solid var(--color-border);
		position: sticky;
		top: 0;
		z-index: 10;
	}
	.marca {
		font-weight: 700;
		font-size: 1.15rem;
		color: var(--color-text);
		text-decoration: none;
	}
	.crece {
		flex: 1;
	}
	.usuario {
		display: inline-flex;
		align-items: center;
		gap: 0.4rem;
		font-weight: 600;
	}
	.hamburguesa {
		display: none;
		background: none;
		border: 0;
		font-size: 1.4rem;
		color: var(--color-text);
		cursor: pointer;
	}
	main {
		padding: 1.25rem;
		min-width: 0;
	}
	@media (max-width: 860px) {
		.app {
			grid-template-columns: minmax(0, 1fr);
		}
		.hamburguesa {
			display: block;
		}
		.usuario {
			display: none;
		}
	}
</style>
