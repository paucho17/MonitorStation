<!--
	Tabs: pestanas de seleccion simple.
	Props: opciones (arreglo de { valor, texto }), value (bindable), onchange.
-->
<script>
	let { opciones = [], value = $bindable(''), onchange = undefined } = $props();

	function elegir(v) {
		value = v;
		onchange?.(v);
	}
</script>

<div class="tabs" role="tablist">
	{#each opciones as o (o.valor)}
		<button
			role="tab"
			class:activa={value === o.valor}
			aria-selected={value === o.valor}
			onclick={() => elegir(o.valor)}>
			{o.texto}
		</button>
	{/each}
</div>

<style>
	.tabs {
		display: flex;
		gap: 0.35rem;
		flex-wrap: wrap;
	}
	button {
		padding: 0.4rem 0.9rem;
		border-radius: 999px;
		border: 1px solid var(--color-border);
		background: var(--color-surface);
		color: var(--color-muted);
		font: inherit;
		font-weight: 600;
		cursor: pointer;
	}
	button.activa {
		background: var(--color-primary);
		border-color: var(--color-primary);
		color: #fff;
	}
</style>
