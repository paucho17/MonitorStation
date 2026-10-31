<!--
	FormularioCrud: formulario generado a partir de la descripcion de una tabla (tablas.js).

	Props:
	  tabla      : entrada del catalogo TABLAS
	  valores    : objeto con los valores (bindable)
	  relaciones : { nombreTabla: [{ id, ...fila }] } para los campos de tipo "relacion"
	  creando    : true al crear (muestra los campos soloCrear y exige las claves)
	  enviando, error, onguardar, oncancelar
-->
<script>
	import Input from './Input.svelte';
	import Select from './Select.svelte';
	import Checkbox from './Checkbox.svelte';
	import Button from './Button.svelte';
	import Alert from './Alert.svelte';

	let {
		tabla,
		valores = $bindable({}),
		relaciones = {},
		creando = false,
		enviando = false,
		error = '',
		onguardar,
		oncancelar
	} = $props();

	const campos = $derived(tabla.campos.filter((c) => creando || !c.soloCrear || c.tipo === 'bool'));
	const soloCrearEditando = $derived(tabla.campos.filter((c) => !creando && c.soloCrear));

	function opciones(campo) {
		if (campo.tipo === 'seleccion') return campo.opciones.map((o) => ({ valor: o, texto: o }));
		const filas = relaciones[campo.tabla] ?? [];
		return filas.map((f) => ({ valor: f.id, texto: String(f[campo.mostrar] ?? f.id) }));
	}

	function enviar(e) {
		e.preventDefault();
		onguardar?.();
	}
</script>

<form onsubmit={enviar}>
	{#if error}<Alert tone="danger" title="No se pudo guardar">{error}</Alert>{/if}

	<div class="formulario">
		{#each campos as campo (campo.nombre)}
			{#if campo.tipo === 'bool'}
				<div class="celda"><Checkbox label={campo.etiqueta} name={campo.nombre} bind:checked={valores[campo.nombre]} /></div>
			{:else if campo.tipo === 'relacion' || campo.tipo === 'seleccion'}
				<Select
					label={campo.etiqueta}
					name={campo.nombre}
					opciones={opciones(campo)}
					requerido={campo.requerido}
					vacio={campo.requerido ? 'Seleccione...' : '(ninguno)'}
					bind:value={valores[campo.nombre]} />
			{:else}
				<div class="celda">
					<Input
						label={campo.etiqueta + (campo.requerido ? ' *' : '')}
						name={campo.nombre}
						type={campo.tipo === 'numero' ? 'number' : campo.tipo === 'clave' ? 'password' : campo.tipo === 'hora' ? 'time' : 'text'}
						bind:value={valores[campo.nombre]} />
					{#if campo.ayuda}<small class="muted">{campo.ayuda}</small>{/if}
				</div>
			{/if}
		{/each}
	</div>

	{#if soloCrearEditando.length}
		<p class="muted">No editables despues de crear: {soloCrearEditando.map((c) => c.etiqueta).join(', ')}.</p>
	{/if}

	<div class="acciones">
		<Button type="submit" disabled={enviando}>{enviando ? 'Guardando...' : 'Guardar'}</Button>
		<Button variant="secondary" onclick={oncancelar}>Cancelar</Button>
	</div>
</form>

<style>
	form {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	.celda {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		justify-content: end;
	}
	.acciones {
		display: flex;
		gap: 0.6rem;
	}
</style>
