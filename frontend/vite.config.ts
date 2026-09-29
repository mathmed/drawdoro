import { defineConfig, loadEnv } from "vite"
import react from "@vitejs/plugin-react"
import path from "path"

import { DEFAULT_APP_NAME } from "./src/config/brandingDefaults"

export default defineConfig(({ mode }) => {
  // index.html uses %VITE_APP_NAME%, which Vite leaves as is when the variable is unset.
  const env = loadEnv(mode, __dirname, "VITE_")
  process.env.VITE_APP_NAME = env.VITE_APP_NAME?.trim() || DEFAULT_APP_NAME

  return {
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
  }
})
