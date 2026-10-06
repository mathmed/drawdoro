import react from '@vitejs/plugin-react'
import path from 'path'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
    // Fixed branding so tests never depend on the product name or on a local .env (forks rename it).
    env: {
      VITE_APP_NAME: 'Test App',
      VITE_APP_SLUG: '',
    },
    // The first dynamic import of a module transforms it cold, which can take seconds on CI runners.
    testTimeout: 20_000,
    restoreMocks: true,
    unstubEnvs: true,
    unstubGlobals: true,
    coverage: {
      provider: 'v8',
      include: ['src/**/*.{ts,tsx}'],
      exclude: ['src/**/*.test.{ts,tsx}', 'src/test/**', 'src/main.tsx', 'src/vite-env.d.ts'],
      reporter: ['text-summary', 'text', 'html', 'json-summary'],
      // The canvas and most views wrap tldraw and are not unit tested, so the global floor is low and
      // only guards against losing what exists. The pure, critical modules must stay well covered.
      thresholds: {
        statements: 10,
        branches: 10,
        functions: 6,
        lines: 10,
        'src/{auth/session,config/branding,config/mcp,config/mcpTools,utils/agents,utils/cursorSender,utils/format,utils/freshness,utils/galleryLabels,utils/presenceLabel,utils/remoteCursors,utils/revisions,utils/validateArchitecture,utils/workspacePresence}.ts': {
          statements: 90,
          branches: 85,
          functions: 90,
          lines: 90,
        },
        'src/store/{useAppStore,useThemeStore,useWorkspacePresenceStore}.ts': {
          statements: 60,
          branches: 55,
          functions: 50,
          lines: 60,
        },
      },
    },
  },
})
