<!--
	Alert: mensaje destacado, con opcion de cerrarlo.
	Props: tone ('info' | 'success' | 'warning' | 'danger'), title, dismissible, children.
-->
<script>
	let { tone = 'info', title = '', dismissible = false, children } = $props();
	let visible = $state(true);
</script>

{#if visible}
	<div class="alert {tone}" role="alert">
		<div>
			{#if title}<strong>{title}</strong>{/if}
			<div>{@render children?.()}</div>
		</div>
		{#if dismissible}
			<button aria-label="Cerrar" onclick={() => (visible = false)}>&times;</button>
		{/if}
	</div>
{/if}

<style>
	.alert {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		padding: 0.85rem 1rem;
		border-radius: var(--radius);
		border-left: 4px solid currentColor;
		background: color-mix(in srgb, currentColor 10%, var(--color-surface));
	}
	.alert div {
		color: var(--color-text);
	}
	.info {
		color: var(--color-info);
	}
	.success {
		color: var(--color-success);
	}
	.warning {
		color: var(--color-warning);
	}
	.danger {
		color: var(--color-danger);
	}
	button {
		background: none;
		border: 0;
		color: inherit;
		font-size: 1.4rem;
		line-height: 1;
		cursor: pointer;
	}
</style>
