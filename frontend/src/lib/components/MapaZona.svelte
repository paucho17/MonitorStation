<script>
	/**
	 * Mapa de la zona de monitoreo (Leaflet).
	 *
	 * Capas base conmutables: OpenTopoMap (topografica, por defecto) y
	 * OpenStreetMap. Dibuja los puntos de referencia GPS agrupados por linea
	 * de muestreo y la ultima posicion reportada por un nodo.
	 *
	 * @prop {Array<{nombre:string, linea?:string, descripcion?:string, latitud:number, longitud:number}>} referencias
	 * @prop {{nodo:string, latitud:number, longitud:number}|null} posicion
	 */
	import { onMount } from 'svelte';
	import L from 'leaflet';
	import 'leaflet/dist/leaflet.css';

	let { referencias = [], posicion = null, alto = '28rem' } = $props();

	let contenedor;
	let mapa;
	let capaPuntos;
	let encuadrado = false; // el encuadre automatico ocurre una sola vez, para respetar el zoom del usuario

	// Un color por linea de muestreo; los puntos sin linea usan el neutro.
	const COLORES = { 'Linea 1': '#1b9e77', 'Linea 2': '#d95f02', 'Linea 3': '#7570b3', 'Linea 4': '#e7298a', 'Linea 5': '#66a61e' };
	const NEUTRO = '#555555';

	function dibujar() {
		if (!mapa) return;
		capaPuntos.clearLayers();
		const encuadre = [];

		for (const r of referencias) {
			const pos = [Number(r.latitud), Number(r.longitud)];
			const esMuelle = !r.linea;
			L.circleMarker(pos, {
				radius: esMuelle ? 8 : 6,
				color: '#ffffff',
				weight: 1.5,
				fillColor: COLORES[r.linea] ?? NEUTRO,
				fillOpacity: 0.95
			})
				.bindTooltip(`${r.nombre}${r.linea ? ' · ' + r.linea : ''}`)
				.bindPopup(
					`<strong>Punto ${r.nombre}</strong><br>${r.linea ?? ''}${r.descripcion ? '<br>' + r.descripcion : ''}` +
						`<br><small>${pos[0].toFixed(6)}, ${pos[1].toFixed(6)}</small>`
				)
				.addTo(capaPuntos);
			// El encuadre ignora puntos aislados (p. ej. el muelle) para no alejar el zoom
			if (r.linea) encuadre.push(pos);
		}

		if (posicion) {
			const pos = [Number(posicion.latitud), Number(posicion.longitud)];
			L.circleMarker(pos, { radius: 9, color: '#c0392b', weight: 3, fillColor: '#ffffff', fillOpacity: 0.6 })
				.bindTooltip(`Nodo ${posicion.nodo}`)
				.addTo(capaPuntos);
			encuadre.push(pos);
		}

		if (encuadre.length && !encuadrado) {
			encuadrado = true;
			mapa.fitBounds(L.latLngBounds(encuadre), { padding: [30, 30], maxZoom: 19 });
		}
	}

	onMount(() => {
		const topo = L.tileLayer('https://tile.opentopomap.org/{z}/{x}/{y}.png', {
			maxZoom: 17,
			attribution:
				'Mapa: &copy; <a href="https://opentopomap.org" target="_blank" rel="noopener noreferrer">OpenTopoMap</a> ' +
				'(<a href="https://creativecommons.org/licenses/by-sa/3.0/" target="_blank" rel="noopener noreferrer">CC-BY-SA</a>), ' +
				'datos &copy; colaboradores de <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a>'
		});
		const osm = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
			maxZoom: 19,
			attribution:
				'&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a>'
		});

		// Centro inicial: Cienaga de Mallorquin; fitBounds lo reemplaza si hay puntos
		mapa = L.map(contenedor, { center: [11.0515, -74.8534], zoom: 17, layers: [topo] });
		L.control.layers({ OpenTopoMap: topo, OpenStreetMap: osm }).addTo(mapa);
		L.control.scale({ imperial: false }).addTo(mapa);
		capaPuntos = L.layerGroup().addTo(mapa);
		dibujar();

		return () => mapa.remove();
	});

	// Redibuja cuando el panel refresca los datos
	$effect(() => {
		referencias;
		posicion;
		dibujar();
	});
</script>

<div bind:this={contenedor} class="mapa" style:height={alto} role="img" aria-label="Mapa de la zona de monitoreo"></div>

<style>
	.mapa {
		width: 100%;
		border-radius: 0.5rem;
		border: 1px solid var(--borde, #d0d7de);
		z-index: 0;
	}
</style>
