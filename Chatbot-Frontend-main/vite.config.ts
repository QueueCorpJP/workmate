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
        target: `http://localhost:${process.env.VITE_BACKEND_PORT || 8085}`,
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
    assetsDir: "assets",
    chunkSizeWarningLimit: 1000,
    sourcemap: false,
    minify: "esbuild",
    target: "es2020",
    commonjsOptions: {
      transformMixedEsModules: true,
    },
    rollupOptions: {
      external: [],
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          mui: ['@mui/material', '@mui/icons-material', '@emotion/react', '@emotion/styled'],
          charts: ['chart.js', 'react-chartjs-2'],
          utils: ['axios', 'react-router-dom', 'react-markdown']
        },
        chunkFileNames: (chunkInfo) => {
          const facadeModuleId = chunkInfo.facadeModuleId ? 
            chunkInfo.facadeModuleId.split('/').pop()?.replace(/\.[^/.]+$/, "") || "chunk" : 
            "chunk";
          return `assets/${facadeModuleId}-[hash].js`;
        },
        assetFileNames: "assets/[name]-[hash].[ext]",
        entryFileNames: "assets/[name]-[hash].js"
      }
    }
  },
  base: "/",
  define: {
    __PROD_API_URL__: JSON.stringify("/chatbot/api"),
    global: "globalThis",
  },
  resolve: {
    alias: {
      "@": resolve(__dirname, "src"),
    },
  },
  esbuild: {
    logOverride: { 
      "this-is-undefined-in-esm": "silent",
      "direct-eval": "silent"
    },
    target: "es2020",
    format: "esm"
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      '@mui/material',
      '@mui/icons-material',
      'chart.js',
      'react-chartjs-2'
    ],
    esbuildOptions: {
      target: "es2020"
    }
  }
});
