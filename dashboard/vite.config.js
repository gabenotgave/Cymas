import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/metrics": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/analysis": {
      target: "http://localhost:8000",
      changeOrigin: true,
    },
    },
  },
});
