import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: path.resolve(__dirname, "../static/frontend"),
    emptyOutDir: true,
    rollupOptions: {
      input: path.resolve(__dirname, "src/main.jsx"),
      output: {
        entryFileNames: "storefront.js",
        chunkFileNames: "chunks/[name].js",
        assetFileNames: (assetInfo) => {
          if ((assetInfo.name || "").endsWith(".css")) {
            return "storefront.css";
          }
          return "assets/[name][extname]";
        },
      },
    },
  },
});
