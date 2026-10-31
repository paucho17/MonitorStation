<!--
	Button: boton o enlace segun reciba href.
	Props: variant ('primary' | 'secondary' | 'ghost' | 'danger'), size ('sm' | 'md' | 'lg'),
	href, type, disabled, onclick, children.
-->
<script>
	let {
		variant = 'primary',
		size = 'md',
		href = undefined,
		type = 'button',
		disabled = false,
		onclick = undefined,
		children
	} = $props();
</script>

{#if href}
	<a class="btn {variant} {size}" {href} aria-disabled={disabled}>
		{@render children?.()}
	</a>
{:else}
	<button class="btn {variant} {size}" {type} {disabled} {onclick}>
		{@render children?.()}
	</button>
{/if}

<style>
	.btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: 0.4rem;
		border: 1px solid transparent;
		border-radius: var(--radius);
		font: inherit;
		font-weight: 600;
		text-decoration: none;
		cursor: pointer;
		transition: background 0.15s, border-color 0.15s;
	}
	.btn:disabled,
	.btn[aria-disabled='true'] {
		opacity: 0.5;
		cursor: not-allowed;
		pointer-events: none;
	}
	.sm {
		padding: 0.3rem 0.7rem;
		font-size: 0.85rem;
	}
	.md {
		padding: 0.55rem 1.1rem;
	}
	.lg {
		padding: 0.8rem 1.6rem;
		font-size: 1.1rem;
	}
	.primary {
		background: var(--color-primary);
		color: #fff;
	}
	.primary:hover {
		background: var(--color-primary-dark);
	}
	.secondary {
		background: var(--color-surface);
		color: var(--color-text);
		border-color: var(--color-border);
	}
	.secondary:hover {
		border-color: var(--color-primary);
	}
	.ghost {
		background: transparent;
		color: var(--color-primary);
	}
	.danger {
		background: var(--color-danger);
		color: #fff;
	}
</style>
