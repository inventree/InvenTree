import { defineConfig, devices } from '@playwright/test';
import type TestConfigWebServer from '@playwright/test';

// Detect if running in CI
const IS_CI = !!process.env.CI;
const IS_COVERAGE = !!process.env.VITE_COVERAGE_BUILD;

// If specified, tests will be run against the production build
const IS_PRODUCTION = !!process.env.VITE_PRODUCTION_BUILD;

console.log('Running Playwright tests:');
console.log(`  - CI Mode: ${IS_CI}`);
console.log(`  - Coverage Mode: ${IS_COVERAGE}`);
console.log(`  - Production Mode: ${IS_PRODUCTION}`);

const MAX_WORKERS: number = 5;
const MAX_RETRIES: number = 5;

/* We optionally spin-up services based on the testing mode:
 *
 * Local Development:
 * - If running locally (developer mode), we run "vite dev" with HMR enabled
 * - This allows playwright to monitor the code for changes
 * - WORKERS = 1 (to avoid conflicts with HMR)
 *
 * CI Mode (PR):
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

const devServer: TestConfigWebServer = {
  command: 'yarn run dev --host --port 5173',
  url: 'http://localhost:5173',
  reuseExistingServer: IS_CI,
  stdout: 'pipe',
  stderr: 'pipe',
  timeout: 120 * 1000
};

// Command to spin-up the backend server
const WEB_SERVER_CMD: string = 'invoke dev.server -a 127.0.0.1:8000';
const WEB_BUILD_CMD: string =
  'yarn run extract && yarn run compile && yarn run build';

const webServer: TestConfigWebServer = {
  // If running in production mode, we need to build the frontend first
  command: IS_PRODUCTION
    ? `${WEB_BUILD_CMD} && ${WEB_SERVER_CMD}`
    : WEB_SERVER_CMD,
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
  url: 'http://127.0.0.1:8000/api/',
  reuseExistingServer: IS_CI,
  stdout: 'pipe',
  stderr: 'pipe',
  timeout: 120 * 1000
};

const serverList: TestConfigWebServer[] = [];

if (!IS_PRODUCTION) {
  serverList.push(devServer);
}

serverList.push(webServer);

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  timeout: 90000,
  forbidOnly: !!IS_CI,
  retries: IS_CI ? MAX_RETRIES : 0,
  workers: IS_PRODUCTION ? MAX_WORKERS : 1,
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
  webServer: serverList,
  use: {
    baseURL: IS_PRODUCTION ? 'http://localhost:8000' : 'http://localhost:5173',
    trace: 'on-first-retry'
  }
});
