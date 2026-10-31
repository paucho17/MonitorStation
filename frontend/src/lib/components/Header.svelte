<!--
	Header: encabezado fijo del sitio; contiene la Navbar.
	Props: brand, links.
-->
<script>
	import Container from './Container.svelte';
	import Navbar from './Navbar.svelte';

	let { brand, links } = $props();
</script>

<header>
	<Container>
		<Navbar {brand} {links} />
	</Container>
</header>

<style>
	header {
		position: sticky;
		top: 0;
		z-index: 10;
		padding-block: 0.8rem;
		background: var(--color-surface);
		border-bottom: 1px solid var(--color-border);
	}
</style>
