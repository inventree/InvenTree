import { defineConfig, devices } from '@playwright/test';

// Detect if running in CI
const IS_CI = !!process.env.CI;

console.log('Running Playwright tests:');
console.log(`  - CI Mode: ${IS_CI}`);

const MAX_WORKERS: number = 3;
const MAX_RETRIES: number = 3;

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
 * - Run a Gunicorn multi-threaded web server to handle multiple requests
 * - WORKERS = MAX_WORKERS (to speed up the tests)
 *
 * CI Mode (Coverage):
 * - In coverage mode (GitHub actions), we cannot compile the code first
 * - This is because we need to compile coverage report against ./src directory
 * - So, we run "vite dev" with coverage enabled (similar to the local dev mode)
 * - WORKERS = 1 (to avoid conflicts with HMR)
 */

// Command to spin-up the backend server
// In production mode, we want a stronger webserver to handle multiple requests
const WEB_SERVER_CMD: string = IS_CI
  ? 'gunicorn --chdir ../backend/InvenTree --workers 8 --thread 8 --bind 127.0.0.1:8000 InvenTree.wsgi'
  : 'cd ../.. && source .venv/bin/activate && invoke dev.server -a 127.0.0.1:8000';

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  timeout: 90000,
  forbidOnly: !!IS_CI,
  retries: IS_CI ? MAX_RETRIES : 0,
  workers: IS_CI ? MAX_WORKERS : 1,
  reporter: IS_CI ? [['html', { open: 'never' }], ['github']] : 'list',

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
      command: WEB_SERVER_CMD,
      env: {
        INVENTREE_DEBUG: 'True',
        INVENTREE_PLUGINS_ENABLED: 'True',
        INVENTREE_ADMIN_URL: 'test-admin',
        INVENTREE_SITE_URL: 'http://localhost:8000',
        INVENTREE_FRONTEND_API_HOST: 'http://localhost:8000',
        INVENTREE_CORS_ORIGIN_ALLOW_ALL: 'True',
        INVENTREE_COOKIE_SAMESITE: 'Lax',
        INVENTREE_LOGIN_ATTEMPTS: '100'
      },
      url: 'http://localhost:8000/api/',
      reuseExistingServer: IS_CI,
      stdout: 'pipe',
      stderr: 'pipe',
      timeout: 120 * 1000
    }
  ],
  globalSetup: './playwright/global-setup.ts',
  use: {
    baseURL: 'http://localhost:5173',
    headless: IS_CI ? true : undefined,
    trace: 'on-first-retry',
    contextOptions: {
      reducedMotion: 'reduce'
    }
  }
});
