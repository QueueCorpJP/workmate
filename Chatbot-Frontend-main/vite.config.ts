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
    outDir: "dist", // ビルド出力先をバックエンドの静的ファイルディレクトリに設定
    emptyOutDir: true,
    assetsDir: "assets", // アセットディレクトリ名を明示的に指定
    chunkSizeWarningLimit: 1000, // チャンクサイズ警告の閾値を1000kBに設定
    rollupOptions: {
      output: {
        manualChunks: {
          // 大きなライブラリを別チャンクに分離
          vendor: ['react', 'react-dom'],
          mui: ['@mui/material', '@mui/icons-material', '@emotion/react', '@emotion/styled'],
          charts: ['chart.js', 'react-chartjs-2'],
          utils: ['axios', 'react-router-dom', 'react-markdown']
        }
      }
    }
  },
  base: "/", // ベースパスを設定
  define: {
    // 本番環境でのフォールバック設定
    __PROD_API_URL__: JSON.stringify("/chatbot/api"),
  },
});
