import { defineConfig, devices } from '@playwright/test';

// Detect if running in CI
const IS_CI = !!process.env.CI;

/* We optionally spin-up services based on the testing mode:
 *
 * Local Development:
 * - If running locally (developer mode), we run "vite dev" with HMR enabled
 * - This allows playwright to monitor the code for changes
 * - WORKERS = 1 (to avoid conflicts with HMR)
 *
 * CI Mode (Production):
 * - In CI (GitHub actions), we run "vite build" to generate a production build
 * - This build is then served by a local server for testing
 * - This allows the tests to run much faster and with parallel workers
 * - WORKERS = MAX_WORKERS (to speed up the tests)
 *
 * CI Mode (Coverage):
 * - In coverage mode (GitHub actions), we cannot compile the code first
 * - This is because we need to compile coverage report against ./src directory
 * - So, we run "vite dev" with coverage enabled (similar to the local dev mode)
 * - WORKERS = 1 (to avoid conflicts with HMR)
 */

const BASE_URL: string =
  process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173';

// If running in "production" mode, we can use multiple workers to speed up the tests
const MAX_WORKERS: number = BASE_URL.endsWith('8000') ? 3 : 1;
const MAX_RETRIES: number = IS_CI ? 1 : 2;

console.log('Running Playwright Tests:');
console.log('- Base URL:', BASE_URL);
console.log('- Max Workers:', MAX_WORKERS);
console.log('- Max Retries:', MAX_RETRIES);

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  timeout: 90000,
  forbidOnly: !!IS_CI,
  retries: MAX_RETRIES,
  workers: MAX_WORKERS,
  reporter: IS_CI
    ? [['html', { open: 'never' }], ['blob'], ['github']]
    : 'list',

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome']
      },
      testIgnore: /customization/ // Ignore all tests in the "customization" folder for this project
    },
    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox']
      }
    }
  ],

  /* Run your local dev server before starting the tests */
  webServer: [
    {
      command: 'yarn run dev --host --port 5173',
      url: 'http://localhost:5173',
      reuseExistingServer: IS_CI,
      stdout: 'pipe',
      stderr: 'pipe',
      timeout: 120 * 1000
    },
    {
      command: 'invoke dev.server -a 0.0.0.0:8000',
      env: {
        INVENTREE_DEBUG: 'True',
        INVENTREE_LOG_LEVEL: 'WARNING',
        INVENTREE_PLUGINS_ENABLED: 'True',
        INVENTREE_ADMIN_URL: 'test-admin',
        INVENTREE_SITE_URL: 'http://localhost:8000',
        INVENTREE_FRONTEND_API_HOST: 'http://localhost:8000',
        INVENTREE_CORS_ORIGIN_ALLOW_ALL: 'True',
        INVENTREE_COOKIE_SAMESITE: 'False',
        INVENTREE_LOGIN_ATTEMPTS: '100',
        INVENTREE_PLUGINS_MANDATORY: 'samplelocate',
        INVENTREE_CUSTOM_SPLASH: 'img/playwright_custom_splash.png',
        INVENTREE_CUSTOM_LOGO: 'img/playwright_custom_logo.png'
      },
      url: 'http://localhost:8000/api/',
      reuseExistingServer: IS_CI,
      stdout: 'pipe',
      stderr: 'pipe',
      timeout: 120 * 1000
    },
    {
      command: 'invoke worker',
      env: {
        INVENTREE_DEBUG: 'True',
        INVENTREE_LOG_LEVEL: 'INFO',
        INVENTREE_PLUGINS_ENABLED: 'True',
        INVENTREE_PLUGINS_MANDATORY: 'samplelocate'
      }
    }
  ],
  globalSetup: './playwright/global-setup.ts',
  use: {
    baseURL: BASE_URL,
    headless: IS_CI ? true : undefined,
    trace: 'on-first-retry',
    contextOptions: {
      reducedMotion: 'reduce'
    }
  }
});
