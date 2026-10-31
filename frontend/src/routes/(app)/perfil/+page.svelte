<script>
	import { onMount } from 'svelte';
	import { api_notificaciones_usuario as api } from '#lib/servicios/datos.js';
	import { sesion } from '#lib/estado/sesion.svelte.js';
	import { Card, Checkbox, Select, Button, Alert, Badge, Spinner } from '#lib';

	let prefs = $state(null);
	let error = $state('');
	let aviso = $state('');
	let guardando = $state(false);

	onMount(async () => {
		try {
			prefs = await api.preferencias();
		} catch (e) {
			error = e.message;
		}
	});

	async function guardar() {
		guardando = true;
		error = aviso = '';
		try {
			await api.guardar({ notificar_alertas: prefs.notificar_alertas, notificar_nivel: prefs.notificar_nivel });
			aviso = 'Preferencias guardadas';
		} catch (e) {
			error = e.message;
		} finally {
			guardando = false;
		}
	}

	async function probar() {
		error = aviso = '';
		try {
			const r = await api.probar();
			aviso = `Correo de prueba enviado a ${r.destino}`;
		} catch (e) {
			error = e.message;
		}
	}
</script>

<svelte:head><title>Mi perfil | IoT-Mangrove</title></svelte:head>

<div class="pagina">
	<h1>Mi perfil</h1>
	{#if aviso}<Alert tone="success" dismissible>{aviso}</Alert>{/if}
	{#if error}<Alert tone="danger" dismissible>{error}</Alert>{/if}

	<div class="doble">
		<Card title="Cuenta">
			<p>Usuario: <strong>{sesion.usuario?.username}</strong></p>
			<p>Correo: {sesion.usuario?.email ?? 'sin correo registrado'}</p>
			<p>Rol: <Badge tone="info">{sesion.usuario?.rol}</Badge></p>
			<p class="muted">Modulos permitidos: {sesion.permisos.filter((p) => p.puede_leer).length}</p>
		</Card>

		<Card title="Avisos de alertas por correo">
			{#if !prefs}
				<Spinner />
			{:else}
				<form onsubmit={(e) => { e.preventDefault(); guardar(); }}>
					<Checkbox label="Enviarme un correo cuando haya alertas" bind:checked={prefs.notificar_alertas} />
					<Select label="Nivel minimo" name="nivel" vacio={null} opciones={[{ valor: 'CRITICO', texto: 'Solo criticas' }, { valor: 'ADVERTENCIA', texto: 'Advertencias y criticas' }]} bind:value={prefs.notificar_nivel} />
					<div class="fila">
						<Button type="submit" disabled={guardando}>Guardar</Button>
						{#if sesion.puede('notificaciones', 'crear')}
							<Button variant="secondary" onclick={probar}>Enviar correo de prueba</Button>
						{/if}
					</div>
					<small class="muted">Para repetir una misma alerta del mismo nodo se espera un tiempo (antirrebote) y evitar saturar su buzon.</small>
				</form>
			{/if}
		</Card>
	</div>
</div>

<style>
	.doble {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(20rem, 1fr));
		gap: 1.25rem;
	}
	form {
		display: flex;
		flex-direction: column;
		gap: 0.9rem;
	}
	.fila {
		display: flex;
		gap: 0.6rem;
		flex-wrap: wrap;
	}
</style>
