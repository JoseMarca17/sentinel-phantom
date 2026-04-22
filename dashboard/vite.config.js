import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    // Autorizamos a ngrok para que Vite no le cierre la puerta
    allowedHosts: [
      'eloisa-unfeasible-iola.ngrok-free.dev'
    ],
    headers: {
      "ngrok-skip-browser-warning": "true",
    },
    proxy: {
      '/api': {
        target: process.env.VITE_PI_API_URL || 'http://192.168.1.50:5000',
        changeOrigin: true,
      },
    },
  },
});