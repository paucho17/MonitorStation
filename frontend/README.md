# IoT-Mangrove: frontend

SvelteKit 3 (runes) como aplicacion de una sola pagina. Documentacion completa en `../docs/FRONTEND.md`.

```bash
npm install
npm run dev        # http://localhost:5173, reenvia /api a localhost:5000 y /aux a localhost:3000
npm run build      # genera build/ (archivos estaticos)
npm run preview    # sirve build/ con el mismo reenvio
```

Con Docker: `docker compose -f docker-compose.yml -f docker-compose.local.yml up --build` desde la raiz del repositorio.
