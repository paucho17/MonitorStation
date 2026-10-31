<!--
	Card: tarjeta con titulo, cuerpo y pie opcional.
	Props: title, children (cuerpo), footer (snippet opcional).
-->
<script>
	let { title = '', children, footer = undefined } = $props();
</script>

<article class="card">
	{#if title}<h3>{title}</h3>{/if}
	<div class="body">{@render children?.()}</div>
	{#if footer}<div class="footer">{@render footer()}</div>{/if}
</article>

<style>
	.card {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		box-shadow: var(--shadow);
		padding: 1.25rem;
		height: 100%;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	.body {
		flex: 1;
		color: var(--color-muted);
	}
	.footer {
		padding-top: 0.75rem;
		border-top: 1px solid var(--color-border);
	}
</style>
