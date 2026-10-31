<script>
	import { goto } from '$app/navigation';
	import { sesion } from '#lib/estado/sesion.svelte.js';
	import { Container, Footer } from '#lib';

	let { children } = $props();

	// Quien ya inicio sesion no necesita ver el acceso
	$effect(() => {
		if (sesion.usuario) goto('/');
	});
</script>

<main class="auth">
	<Container size="sm">
		<div class="marca">
			<h1>IoT-Mangrove</h1>
			<p class="muted">Monitoreo ambiental de manglares y riego del vivero</p>
		</div>
		{@render children()}
	</Container>
</main>
<Footer text="IoT-Mangrove, Universidad IUB. Barranquilla, Colombia." />

<style>
	.auth {
		min-height: 70vh;
		display: grid;
		align-items: center;
		padding-block: 2rem;
	}
	.marca {
		text-align: center;
		margin-bottom: 1.25rem;
	}
</style>
