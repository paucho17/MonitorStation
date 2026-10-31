<!--
	Input: campo de formulario con etiqueta y mensaje de error.
	Props: label, name, type, placeholder, error, value (bindable).
-->
<script>
	let {
		label,
		name,
		type = 'text',
		placeholder = '',
		error = '',
		value = $bindable('')
	} = $props();

	const id = $props.id();
</script>

<div class="field">
	<label for="{id}-{name}">{label}</label>
	<input id="{id}-{name}" {name} {type} {placeholder} bind:value aria-invalid={!!error} />
	{#if error}<small class="error">{error}</small>{/if}
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
	input {
		padding: 0.55rem 0.75rem;
		font: inherit;
		color: var(--color-text);
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
	}
	input:focus {
		outline: 2px solid var(--color-primary);
		outline-offset: 1px;
	}
	input[aria-invalid='true'] {
		border-color: var(--color-danger);
	}
	.error {
		color: var(--color-danger);
	}
</style>
