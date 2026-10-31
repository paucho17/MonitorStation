<script>
	import favicon from '#lib/assets/favicon.svg';
	import '#lib/styles/global.css';
	import { sesion } from '#lib/estado/sesion.svelte.js';
	import { onMount } from 'svelte';

	let { children } = $props();

	// Si hay un token guardado, recupera el usuario y sus permisos
	onMount(() => {
		if (sesion.token && !sesion.usuario) sesion.cargarPerfil();
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>IoT-Mangrove</title>
</svelte:head>

{@render children()}
