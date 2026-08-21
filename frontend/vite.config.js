import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Ruta pública desde la que se sirve la aplicación.
//
//   Producción  https://pablocabello.eu/seismos/   ->  VITE_BASE_PATH=/seismos/
//   Desarrollo (`npm run dev`) y `docker compose up` en localhost:8080  ->  '/'
//
// El despliegue actual ya se construye con la base '/seismos/' (el HTML servido
// referencia /seismos/assets/...), pero esa base se pasaba a mano y no estaba en
// el repositorio: `npm run build` no reproducía producción. Esta variable lo deja
// escrito sin cambiar el comportamiento por defecto.
const base = process.env.VITE_BASE_PATH || '/';

export default defineConfig({
  base,
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
  },
});
