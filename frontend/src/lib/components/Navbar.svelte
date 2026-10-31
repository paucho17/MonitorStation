<!--
	Navbar: barra de navegacion con menu responsive.
	Props: brand (texto), links (arreglo de { href, label }).
-->
<script>
	import { page } from '$app/state';

	let { brand = 'Mi Proyecto', links = [] } = $props();
	let open = $state(false);
</script>

<nav class="navbar" aria-label="Principal">
	<a class="brand" href="/">{brand}</a>
	<button
		class="toggle"
		aria-label="Abrir menu"
		aria-expanded={open}
		onclick={() => (open = !open)}>
		<span></span><span></span><span></span>
	</button>
	<ul class:open>
		{#each links as link (link.href)}
			<li>
				<a
					href={link.href}
					aria-current={page.url.pathname === link.href ? 'page' : undefined}
					onclick={() => (open = false)}>
					{link.label}
				</a>
			</li>
		{/each}
	</ul>
</nav>

<style>
	.navbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: 1rem;
	}
	.brand {
		font-weight: 700;
		font-size: 1.2rem;
		text-decoration: none;
		color: var(--color-text);
	}
	ul {
		display: flex;
		gap: 1.25rem;
		list-style: none;
		margin: 0;
		padding: 0;
	}
	li a {
		text-decoration: none;
		color: var(--color-muted);
		font-weight: 500;
	}
	li a:hover,
	li a[aria-current='page'] {
		color: var(--color-primary);
	}
	.toggle {
		display: none;
		flex-direction: column;
		gap: 4px;
		background: none;
		border: 0;
		padding: 0.4rem;
		cursor: pointer;
	}
	.toggle span {
		width: 22px;
		height: 2px;
		background: var(--color-text);
	}
	@media (max-width: 640px) {
		.toggle {
			display: flex;
		}
		ul {
			display: none;
			flex-direction: column;
			width: 100%;
		}
		ul.open {
			display: flex;
		}
	}
</style>
