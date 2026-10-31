<!--
	Badge: etiqueta corta de estado.
	Props: tone ('neutral' | 'info' | 'success' | 'warning' | 'danger'), children.
-->
<script>
	let { tone = 'neutral', children } = $props();
</script>

<span class="badge {tone}">{@render children?.()}</span>

<style>
	.badge {
		display: inline-block;
		padding: 0.1rem 0.6rem;
		border-radius: 999px;
		font-size: 0.8rem;
		font-weight: 600;
		border: 1px solid currentColor;
	}
	.neutral {
		color: var(--color-muted);
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
</style>
