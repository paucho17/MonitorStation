<!--
	Medidor: tarjeta de una variable (nombre, valor, unidad, estado de alerta, nodo y hora).
	Props: nombre, valor, unidad, nivel (null | 'ADVERTENCIA' | 'CRITICO'), nodo, fecha.
-->
<script>
	let { nombre, valor, unidad = '', nivel = null, nodo = '', fecha = '' } = $props();

	const texto = $derived(typeof valor === 'number' ? Number(valor.toFixed(2)) : valor);
	const hora = $derived(fecha ? new Date(fecha).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' }) : '');
</script>

<div class="medidor {nivel ?? 'normal'}">
	<span class="nombre">{nombre}</span>
	<span class="valor">{texto}<small>{unidad}</small></span>
	<span class="pie">
		{#if nivel}<strong>{nivel === 'CRITICO' ? 'Critica' : 'Advertencia'}</strong>{/if}
		<span>Nodo {nodo}</span>
		{#if hora}<span>{hora}</span>{/if}
	</span>
</div>

<style>
	.medidor {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
		padding: 1rem;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-left: 5px solid var(--color-accent);
		border-radius: var(--radius);
		box-shadow: var(--shadow);
	}
	.ADVERTENCIA {
		border-left-color: var(--color-warning);
	}
	.CRITICO {
		border-left-color: var(--color-danger);
	}
	.nombre {
		color: var(--color-muted);
		font-size: 0.9rem;
	}
	.valor {
		font-size: 1.9rem;
		font-weight: 700;
	}
	.valor small {
		font-size: 0.95rem;
		font-weight: 500;
		margin-left: 0.3rem;
		color: var(--color-muted);
	}
	.pie {
		display: flex;
		flex-wrap: wrap;
		gap: 0.2rem 0.8rem;
		font-size: 0.8rem;
		color: var(--color-muted);
	}
	.ADVERTENCIA .pie strong {
		color: var(--color-warning);
	}
	.CRITICO .pie strong {
		color: var(--color-danger);
	}
</style>
