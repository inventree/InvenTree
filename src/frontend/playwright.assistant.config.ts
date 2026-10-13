import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  testMatch: [
    'pui_cangxu_assistant_component.spec.ts',
    'pui_cangxu_assistant_workbench.spec.ts'
  ],
  outputDir: './test-results/assistant',
  timeout: 30000,
  workers: 1,
  retries: 0,
  reporter: 'list',
  use: {
    ...devices['Desktop Chrome'],
    baseURL: 'http://localhost:5173',
    headless: true,
    reducedMotion: 'reduce'
  },
  webServer: {
    command: 'yarn dev --host 127.0.0.1 --port 5173',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120000
  }
});
