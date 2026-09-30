import { defineConfig } from '@playwright/test'

// Visual QA: screenshots every screen at the handoff sizes (360×800 and 1440×900)
// into tests/visual/__shots__ for side-by-side comparison with design_handoff_speakwise/screenshots.
const PORT = 5178

export default defineConfig({
  testDir: 'tests/visual',
  fullyParallel: true,
  // A few workers keep the Vite dev server responsive during full runs.
  workers: 3,
  reporter: 'list',
  use: {
    baseURL: `http://localhost:${PORT}`,
    // Fake camera + mic so the record flow can be captured headlessly.
    permissions: ['camera', 'microphone'],
    launchOptions: {
      args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'],
    },
  },
  projects: [
    { name: 'mobile', use: { viewport: { width: 360, height: 800 }, deviceScaleFactor: 2, hasTouch: true } },
    { name: 'desktop', use: { viewport: { width: 1440, height: 900 } } },
  ],
  webServer: {
    command: `npm run dev -- --port ${PORT} --strictPort`,
    url: `http://localhost:${PORT}`,
    reuseExistingServer: true,
  },
})
