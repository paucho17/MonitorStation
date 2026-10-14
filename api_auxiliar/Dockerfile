# Imagen de la API auxiliar (Express)
FROM node:22-alpine

ENV NODE_ENV=production
WORKDIR /srv

COPY package.json package-lock.json* ./
RUN npm install --omit=dev && npm cache clean --force

COPY src ./src

USER node
EXPOSE 3000

CMD ["node", "src/index.js"]
