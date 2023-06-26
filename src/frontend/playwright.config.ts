import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: 'html',

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome']
      }
    },
    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox']
      }
    }
  ],

  /* Run your local dev server before starting the tests */
  webServer: {
    command:
      'export INVENTREE_DEBUG=True && exportINVENTREE_LOG_LEVEL=DEBUG && export TESTING=True && invoke server -a 127.0.0.1:8000 -c',
    url: 'http://127.0.0.1:8000/api/',
    reuseExistingServer: !process.env.CI,
    stdout: 'pipe',
    stderr: 'pipe',
    timeout: 120 * 1000
  },
  use: {
    baseURL: 'http://127.0.0.1:8000',
    trace: 'on-first-retry'
  }
});
