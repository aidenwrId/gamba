import { defineConfig } from "vite";
import { resolve } from "path";

export default defineConfig({
  root: __dirname,
  build: {
    outDir: "dist",
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, "index.html"),
        about: resolve(__dirname, "about.html"),
        faq: resolve(__dirname, "faq.html"),
        terms: resolve(__dirname, "terms.html"),
      },
    },
  },
});
