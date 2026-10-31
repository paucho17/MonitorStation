<script>
	import { goto } from '$app/navigation';
	import { sesion } from '#lib/estado/sesion.svelte.js';
	import { Card, Input, Button, Alert } from '#lib';

	let username = $state('');
	let password = $state('');
	let error = $state('');
	let enviando = $state(false);

	async function entrar(e) {
		e.preventDefault();
		error = '';
		enviando = true;
		try {
			await sesion.iniciar(username.trim(), password);
			await goto('/');
		} catch (err) {
			error = err.message;
		} finally {
			enviando = false;
		}
	}
</script>

<svelte:head><title>Iniciar sesion | IoT-Mangrove</title></svelte:head>

<Card title="Iniciar sesion">
	<form onsubmit={entrar}>
		{#if error}<Alert tone="danger">{error}</Alert>{/if}
		<Input label="Usuario" name="username" bind:value={username} />
		<Input label="Contrasena" name="password" type="password" bind:value={password} />
		<Button type="submit" disabled={enviando || !username || !password}>{enviando ? 'Ingresando...' : 'Ingresar'}</Button>
	</form>
	{#snippet footer()}
		<span class="muted">¿No tiene cuenta? <a href="/registro">Registrese</a></span>
	{/snippet}
</Card>

<style>
	form {
		display: flex;
		flex-direction: column;
		gap: 0.9rem;
	}
</style>
