import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

// En desarrollo y en vista previa, /api y /aux se reenvian a las APIs locales
// (puertos de docker-compose.dev.yml). En produccion lo hace Nginx.
const proxy = {
	'/api': { target: process.env.API_URL ?? 'http://localhost:5000', changeOrigin: true },
	'/aux': {
		target: process.env.API_AUX_URL ?? 'http://localhost:3000',
		changeOrigin: true,
		rewrite: (ruta) => ruta.replace(/^\/aux/, '')
	}
};

export default defineConfig({
	plugins: [
		sveltekit({
			compilerOptions: {
				// Modo runes en todo el proyecto, salvo en dependencias
				runes: ({ filename }) =>
					filename.split(/[/\\]/).includes('node_modules') ? undefined : true
			},
			// Aplicacion de una sola pagina: se genera HTML estatico con
			// index.html como alternativa para cualquier ruta.
			adapter: adapter({ fallback: 'index.html' })
		})
	],
	// VITE_USE_POLLING=true: necesario para detectar cambios en carpetas montadas desde Windows
	server: { host: true, proxy, watch: process.env.VITE_USE_POLLING ? { usePolling: true } : undefined },
	preview: { host: true, proxy }
});
