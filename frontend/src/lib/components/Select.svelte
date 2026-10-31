<!--
	Select: lista desplegable con etiqueta.
	Props: label, name, opciones (arreglo de { valor, texto }), vacio (texto de la opcion en blanco),
	requerido, value (bindable).
-->
<script>
	let { label, name, opciones = [], vacio = '', requerido = false, value = $bindable(''), onchange = undefined } = $props();
	const id = $props.id();
</script>

<div class="field">
	<label for="{id}-{name}">{label}{#if requerido}<span aria-hidden="true"> *</span>{/if}</label>
	<select id="{id}-{name}" {name} required={requerido} bind:value {onchange}>
		{#if vacio !== null}<option value="">{vacio}</option>{/if}
		{#each opciones as o (o.valor)}
			<option value={o.valor}>{o.texto}</option>
		{/each}
	</select>
</div>

<style>
	.field {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}
	label {
		font-weight: 600;
		font-size: 0.9rem;
	}
	select {
		padding: 0.55rem 0.75rem;
		font: inherit;
		color: var(--color-text);
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
	}
	select:focus {
		outline: 2px solid var(--color-primary);
		outline-offset: 1px;
	}
</style>
