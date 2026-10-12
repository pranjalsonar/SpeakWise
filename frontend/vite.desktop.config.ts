import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Desktop (Electron) renderer: separate entry, relative asset paths for file:// loading.
export default defineConfig({
  plugins: [react()],
  base: './',
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    outDir: 'dist-desktop',
    emptyOutDir: true,
    rollupOptions: { input: fileURLToPath(new URL('./desktop.html', import.meta.url)) },
  },
})
