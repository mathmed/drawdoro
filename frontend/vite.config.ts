import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import path from "path"

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  // Bundle the TipTap extensions in the same pass as tldraw so they share a single
  // @tiptap/core/ProseMirror instance (two copies break the rich text editor).
  optimizeDeps: {
    include: [
      "tldraw",
      "@tiptap/extension-color",
      "@tiptap/extension-highlight",
      "@tiptap/extension-link",
      "@tiptap/extension-text-style",
    ],
  },
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        rewrite: (path) => path.replace(/^\/api/, ""),
        ws: true,
      },
    },
  },
})
