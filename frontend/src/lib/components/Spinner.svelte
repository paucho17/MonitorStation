<!--
	Spinner: indicador de carga.
	Props: texto (accesible, tambien visible).
-->
<script>
	let { texto = 'Cargando...' } = $props();
</script>

<div class="spinner" role="status" aria-live="polite">
	<span class="rueda"></span>
	<span>{texto}</span>
</div>

<style>
	.spinner {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		color: var(--color-muted);
		padding: 1rem 0;
	}
	.rueda {
		width: 1.2rem;
		height: 1.2rem;
		border: 3px solid var(--color-border);
		border-top-color: var(--color-primary);
		border-radius: 50%;
		animation: girar 0.8s linear infinite;
	}
	@keyframes girar {
		to {
			transform: rotate(360deg);
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.rueda {
			animation-duration: 3s;
		}
	}
</style>
