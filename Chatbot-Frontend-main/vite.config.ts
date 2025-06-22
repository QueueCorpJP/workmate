import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3025,
    host: "0.0.0.0",
    proxy: {
      "/chatbot/api": {
        target: `http://localhost:${process.env.VITE_BACKEND_PORT || 8083}`,
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
    assetsDir: "static",
    chunkSizeWarningLimit: 1000,
    sourcemap: false,
    minify: "esbuild",
    target: "es2020",
    commonjsOptions: {
      transformMixedEsModules: true,
    },
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          mui: ['@mui/material', '@mui/icons-material'],
          charts: ['chart.js', 'react-chartjs-2'],
          router: ['react-router-dom']
        },
        chunkFileNames: "static/js/[name]-[hash].js",
        entryFileNames: "static/js/[name]-[hash].js",
        assetFileNames: "static/[ext]/[name]-[hash].[ext]"
      }
    }
  },
  base: "./",
  publicDir: "public",
  define: {
    global: "globalThis",
  },
  resolve: {
    alias: {
      "@": resolve(__dirname, "src"),
    },
  },
  esbuild: {
    target: "es2020",
    format: "esm"
  }
});
