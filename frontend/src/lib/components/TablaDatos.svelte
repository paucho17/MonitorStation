<!--
	TablaDatos: tabla con la libreria DataTables (busqueda, orden y paginacion).

	Props:
	  columnas : [{ titulo, campo, formato?(valor, fila) -> texto, tipo?: 'bool'|'fecha' }]
	  filas    : arreglo de objetos
	  acciones : [{ id, texto, clase?, visible?(fila) -> bool }]  (botones por fila)
	  onaccion : (idAccion, fila) => void

	Todo el texto se escapa antes de llegar al DOM. Los botones usan delegacion de eventos
	(data-accion y data-indice) para no depender de HTML dinamico con manejadores.
-->
<script>
	import DataTable from 'datatables.net-dt';
	import 'datatables.net-dt/css/dataTables.dataTables.css';

	let { columnas = [], filas = [], acciones = [], onaccion = undefined, orden = [[0, 'desc']] } = $props();

	let tabla;
	let contenedor;

	const idioma = {
		search: 'Buscar:',
		lengthMenu: 'Mostrar _MENU_',
		info: 'Mostrando _START_ a _END_ de _TOTAL_',
		infoEmpty: 'Sin registros',
		infoFiltered: '(filtrado de _MAX_)',
		zeroRecords: 'No hay coincidencias',
		emptyTable: 'No hay datos',
		paginate: { first: 'Primero', last: 'Ultimo', next: 'Siguiente', previous: 'Anterior' }
	};

	/** Escapa HTML para insertar texto de la API de forma segura. */
	function escapar(texto) {
		return String(texto ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
	}

	function celda(columna, fila) {
		const bruto = fila[columna.campo];
		if (columna.formato) return columna.formato(bruto, fila);
		if (columna.tipo === 'bool') return bruto ? 'Si' : 'No';
		if (columna.tipo === 'fecha') return bruto ? new Date(bruto).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' }) : '';
		return bruto ?? '';
	}

	$effect(() => {
		// Dependencias reactivas
		const cols = columnas;
		const datos = filas;
		const acc = acciones;
		const ordenar = orden;
		if (!contenedor) return;

		const definicion = cols.map((c) => ({
			title: c.titulo,
			data: null,
			render: (_d, tipo, fila) => {
				const texto = celda(c, fila);
				// Para ordenar fechas y numeros se usa el valor crudo
				if (tipo === 'sort' || tipo === 'type') return c.tipo === 'fecha' ? (fila[c.campo] ?? '') : (typeof fila[c.campo] === 'number' ? fila[c.campo] : texto);
				return escapar(texto);
			}
		}));
		if (acc.length) {
			definicion.push({
				title: '',
				data: null,
				orderable: false,
				searchable: false,
				render: (_d, tipo, fila) => {
					if (tipo !== 'display') return '';
					const indice = datos.indexOf(fila);
					return acc
						.filter((a) => !a.visible || a.visible(fila))
						.map((a) => `<button type="button" class="btn-tabla ${escapar(a.clase ?? '')}" data-accion="${escapar(a.id)}" data-indice="${indice}">${escapar(a.texto)}</button>`)
						.join(' ');
				}
			});
		}

		tabla = new DataTable(contenedor, {
			data: datos,
			columns: definicion,
			order: ordenar,
			pageLength: 25,
			language: idioma,
			layout: { topStart: 'pageLength', topEnd: 'search', bottomStart: 'info', bottomEnd: 'paging' }
		});

		return () => {
			tabla?.destroy();
			tabla = undefined;
			if (contenedor) contenedor.innerHTML = '';
		};
	});

	function clic(evento) {
		const boton = evento.target.closest('button[data-accion]');
		if (!boton || !onaccion) return;
		const fila = filas[Number(boton.dataset.indice)];
		if (fila) onaccion(boton.dataset.accion, fila);
	}
</script>

<div class="envoltura" onclick={clic} role="presentation">
	<table bind:this={contenedor} class="display" style="width:100%"></table>
</div>

<style>
	.envoltura {
		overflow-x: auto;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		padding: 0.75rem;
	}
	.envoltura :global(.btn-tabla) {
		padding: 0.2rem 0.6rem;
		border-radius: 0.4rem;
		border: 1px solid var(--color-border);
		background: var(--color-surface);
		color: var(--color-text);
		font: inherit;
		font-size: 0.8rem;
		cursor: pointer;
	}
	.envoltura :global(.btn-tabla:hover) {
		border-color: var(--color-primary);
	}
	.envoltura :global(.btn-tabla.peligro) {
		color: var(--color-danger);
	}
	.envoltura :global(table.dataTable) {
		color: var(--color-text);
	}
</style>
