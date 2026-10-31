<!--
	Sidebar: menu lateral agrupado, adaptable a movil.
	Props: grupos (arreglo de { titulo, enlaces: [{ href, texto }] }), open (bindable, solo movil).
-->
<script>
	import { page } from '$app/state';

	let { grupos = [], open = $bindable(false) } = $props();
</script>

<aside class:open aria-label="Menu lateral">
	<nav>
		{#each grupos as grupo (grupo.titulo)}
			<h4>{grupo.titulo}</h4>
			<ul>
				{#each grupo.enlaces as e (e.href)}
					<li>
						<a
							href={e.href}
							aria-current={page.url.pathname === e.href || page.url.pathname.startsWith(e.href + '/') ? 'page' : undefined}
							onclick={() => (open = false)}>{e.texto}</a>
					</li>
				{/each}
			</ul>
		{/each}
	</nav>
</aside>

<style>
	aside {
		background: var(--color-surface);
		border-right: 1px solid var(--color-border);
		padding: 1rem;
		overflow-y: auto;
	}
	h4 {
		margin: 1rem 0 0.3rem;
		font-size: 0.75rem;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--color-muted);
	}
	h4:first-child {
		margin-top: 0;
	}
	ul {
		list-style: none;
		margin: 0;
		padding: 0;
	}
	a {
		display: block;
		padding: 0.35rem 0.6rem;
		border-radius: var(--radius);
		color: var(--color-text);
		text-decoration: none;
	}
	a:hover {
		background: var(--color-bg);
	}
	a[aria-current='page'] {
		background: color-mix(in srgb, var(--color-primary) 14%, transparent);
		color: var(--color-primary);
		font-weight: 600;
	}
	@media (max-width: 860px) {
		aside {
			position: fixed;
			inset: 0 auto 0 0;
			width: 16rem;
			z-index: 20;
			transform: translateX(-100%);
			transition: transform 0.2s;
		}
		aside.open {
			transform: none;
			box-shadow: var(--shadow);
		}
	}
</style>
