<!--
	Section: seccion de pagina con titulo y descripcion opcionales.
	Props: title, description, children.
-->
<script>
	let { title = '', description = '', children } = $props();
</script>

<section>
	{#if title}<h2>{title}</h2>{/if}
	{#if description}<p class="desc">{description}</p>{/if}
	{@render children?.()}
</section>

<style>
	section {
		padding-block: 2rem;
	}
	.desc {
		color: var(--color-muted);
		margin: 0 0 1.25rem;
	}
</style>
