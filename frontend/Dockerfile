FROM node:22-alpine AS build
WORKDIR /app
ENV VITE_API_BASE_URL=""
# Ruta pública de la aplicación. Por defecto '/' (docker compose local).
# Para pablocabello.eu/seismos/:  docker build --build-arg VITE_BASE_PATH=/seismos/ .
ARG VITE_BASE_PATH=/
ENV VITE_BASE_PATH=$VITE_BASE_PATH
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
