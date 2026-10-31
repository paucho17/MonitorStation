<!--
	Modal: dialogo modal accesible basado en <dialog>.
	Props: title, open (bindable), onclose (se llama al cerrar), children.
	Cierra con Escape, con el boton o al hacer clic fuera del cuadro.
-->
<script>
	let { title = '', open = $bindable(false), onclose = undefined, children } = $props();
	let dialog;

	$effect(() => {
		if (!dialog) return;
		if (open && !dialog.open) dialog.showModal();
		if (!open && dialog.open) dialog.close();
	});
</script>

<dialog bind:this={dialog} onclose={() => { open = false; onclose?.(); }} onclick={(e) => e.target === dialog && (open = false)}>
	<div class="box">
		<div class="head">
			<h3>{title}</h3>
			<button aria-label="Cerrar" onclick={() => (open = false)}>&times;</button>
		</div>
		{@render children?.()}
	</div>
</dialog>

<style>
	dialog {
		border: 0;
		padding: 0;
		border-radius: var(--radius);
		background: var(--color-surface);
		color: var(--color-text);
		box-shadow: var(--shadow);
		width: min(32rem, 92vw);
	}
	dialog::backdrop {
		background: rgb(15 23 42 / 0.55);
	}
	.box {
		padding: 1.25rem;
	}
	.head {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.75rem;
	}
	.head h3 {
		margin: 0;
	}
	button {
		background: none;
		border: 0;
		font-size: 1.5rem;
		color: var(--color-muted);
		cursor: pointer;
	}
</style>
