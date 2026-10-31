# syntax=docker/dockerfile:1
# Frontend de IoT-Mangrove: compila SvelteKit (adapter-static) y lo sirve con Nginx.

# --- Etapa 1: compilacion ---
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json .npmrc ./
RUN npm ci
COPY . .
RUN npm run build

# --- Etapa 2: servidor estatico ---
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
