<!--
	Footer: pie de pagina con texto de derechos y enlaces opcionales.
	Props: text, links (arreglo de { href, label }).
-->
<script>
	import Container from './Container.svelte';

	let { text = `${new Date().getFullYear()} Mi Proyecto. Todos los derechos reservados.`, links = [] } =
		$props();
</script>

<footer>
	<Container>
		<div class="row">
			<small>{text}</small>
			{#if links.length}
				<ul>
					{#each links as link (link.href)}
						<li><a href={link.href}>{link.label}</a></li>
					{/each}
				</ul>
			{/if}
		</div>
	</Container>
</footer>

<style>
	footer {
		margin-top: 3rem;
		padding-block: 1.5rem;
		border-top: 1px solid var(--color-border);
		color: var(--color-muted);
	}
	.row {
		display: flex;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: 0.75rem;
	}
	ul {
		display: flex;
		gap: 1rem;
		list-style: none;
		margin: 0;
		padding: 0;
	}
</style>
