<script>
	import { goto } from '$app/navigation';
	import { api_registro } from '#lib/servicios/datos.js';
	import { Card, Input, Button, Alert } from '#lib';

	let datos = $state({ username: '', email: '', nombre_completo: '', password: '' });
	let error = $state('');
	let listo = $state(false);
	let enviando = $state(false);

	async function registrar(e) {
		e.preventDefault();
		error = '';
		enviando = true;
		try {
			await api_registro.crear({
				username: datos.username.trim(),
				password: datos.password,
				email: datos.email.trim() || undefined,
				nombre_completo: datos.nombre_completo.trim() || undefined
			});
			listo = true;
			setTimeout(() => goto('/login'), 1500);
		} catch (err) {
			error = err.message;
		} finally {
			enviando = false;
		}
	}
</script>

<svelte:head><title>Registro | IoT-Mangrove</title></svelte:head>

<Card title="Crear cuenta">
	{#if listo}
		<Alert tone="success">Cuenta creada. Redirigiendo al inicio de sesion...</Alert>
	{:else}
		<form onsubmit={registrar}>
			{#if error}<Alert tone="danger">{error}</Alert>{/if}
			<Input label="Usuario (minimo 3 caracteres)" name="username" bind:value={datos.username} />
			<Input label="Nombre completo" name="nombre_completo" bind:value={datos.nombre_completo} />
			<Input label="Correo" name="email" type="email" bind:value={datos.email} />
			<Input label="Contrasena (minimo 6 caracteres)" name="password" type="password" bind:value={datos.password} />
			<Button type="submit" disabled={enviando || datos.username.length < 3 || datos.password.length < 6}>
				{enviando ? 'Creando...' : 'Registrarme'}
			</Button>
			<p class="muted">Las cuentas nuevas tienen rol de consulta. Un administrador puede cambiarlo.</p>
		</form>
	{/if}
	{#snippet footer()}
		<a href="/login">Volver a iniciar sesion</a>
	{/snippet}
</Card>

<style>
	form {
		display: flex;
		flex-direction: column;
		gap: 0.9rem;
	}
</style>
