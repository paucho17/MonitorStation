<!--
	Checkbox: casilla con etiqueta.
	Props: label, name, checked (bindable), disabled.
-->
<script>
	let { label, name = '', checked = $bindable(false), disabled = false } = $props();
</script>

<label class="check">
	<input type="checkbox" {name} bind:checked {disabled} />
	<span>{label}</span>
</label>

<style>
	.check {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		cursor: pointer;
	}
	input {
		width: 1.1rem;
		height: 1.1rem;
		accent-color: var(--color-primary);
	}
</style>
