<!--
	Hero: bloque de presentacion con titulo, subtitulo y acciones.
	Props: title, subtitle, children (zona de botones).
-->
<script>
	let { title, subtitle = '', children } = $props();
</script>

<section class="hero">
	<h1>{title}</h1>
	{#if subtitle}<p>{subtitle}</p>{/if}
	<div class="actions">{@render children?.()}</div>
</section>

<style>
	.hero {
		text-align: center;
		padding: 4rem 1rem;
	}
	h1 {
		font-size: clamp(2rem, 5vw, 3.25rem);
	}
	p {
		max-width: 40rem;
		margin: 0 auto 1.5rem;
		color: var(--color-muted);
		font-size: 1.15rem;
	}
	.actions {
		display: flex;
		justify-content: center;
		gap: 0.75rem;
		flex-wrap: wrap;
	}
</style>
