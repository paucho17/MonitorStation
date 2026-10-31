<!--
	Container: limita el ancho del contenido y lo centra.
	Props: size ('sm' | 'md' | 'lg'), children.
-->
<script>
	let { size = 'lg', children } = $props();
</script>

<div class="container {size}">
	{@render children?.()}
</div>

<style>
	.container {
		width: 100%;
		margin-inline: auto;
		padding-inline: 1rem;
	}
	.sm {
		max-width: 40rem;
	}
	.md {
		max-width: 56rem;
	}
	.lg {
		max-width: var(--max-width);
	}
</style>
