<!--
	Grid: cuadricula responsive de columnas iguales.
	Props: min (ancho minimo de columna, CSS), gap (CSS), children.
-->
<script>
	let { min = '16rem', gap = '1.25rem', children } = $props();
</script>

<div class="grid" style:--min={min} style:--gap={gap}>
	{@render children?.()}
</div>

<style>
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(var(--min), 1fr));
		gap: var(--gap);
	}
</style>
