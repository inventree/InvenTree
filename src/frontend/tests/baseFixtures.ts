import * as crypto from 'node:crypto';
import * as fs from 'node:fs';
import os from 'node:os';
import * as path from 'node:path';
import { type BrowserContext, test as baseTest } from '@playwright/test';

const istanbulCLIOutput = path.join(process.cwd(), '.nyc_output');
const platform = os.platform();
let systemKeyVar: string;
if (platform === 'darwin') {
  systemKeyVar = 'Meta';
} else {
  systemKeyVar = 'Control';
}
/* metaKey is the local action key (used for spotlight for example) */
export const systemKey = systemKeyVar;

export function generateUUID(): string {
  return crypto.randomBytes(16).toString('hex');
}

async function setupCoverageCollection(context: BrowserContext) {
  await context.addInitScript(() =>
    window.addEventListener('beforeunload', () =>
      (window as any).collectIstanbulCoverage?.(
        JSON.stringify((window as any).__coverage__)
      )
    )
  );
  await fs.promises.mkdir(istanbulCLIOutput, { recursive: true });
  try {
    await context.exposeFunction(
      'collectIstanbulCoverage',
      (coverageJSON: string) => {
        if (coverageJSON)
          fs.writeFileSync(
            path.join(
              istanbulCLIOutput,
              `playwright_coverage_${generateUUID()}.json`
            ),
            coverageJSON
          );
      }
    );
  } catch {
    // already exposed on this context (e.g. called twice for same context)
  }
}

async function collectCoverageFromContext(context: BrowserContext) {
  for (const page of context.pages()) {
    try {
      await page.evaluate(() =>
        (window as any).collectIstanbulCoverage?.(
          JSON.stringify((window as any).__coverage__)
        )
      );
    } catch {
      // page may already be closed
    }
  }
}

export const test = baseTest.extend<{}, {}>({
  // Wrap browser.newPage so contexts created via doCachedLogin also get coverage
  browser: [
    async ({ browser }, use) => {
      const origNewPage = browser.newPage.bind(browser);
      (browser as any).newPage = async (
        options?: Parameters<typeof browser.newPage>[0]
      ) => {
        const page = await origNewPage(options);
        await setupCoverageCollection(page.context());
        return page;
      };
      await use(browser);
      for (const context of browser.contexts()) {
        await collectCoverageFromContext(context);
      }
    },
    { scope: 'worker' }
  ],

  context: async ({ context }, use) => {
    await setupCoverageCollection(context);
    await use(context);
    await collectCoverageFromContext(context);
  },

  // Ensure no errors are thrown in the console
  page: async ({ page }, use) => {
    const messages: any[] = [];
    page.on('console', (msg) => {
      const url = msg.location().url;
      if (
        msg.type() === 'error' &&
        !msg.text().startsWith('ERR: ') &&
        msg.text().indexOf('downloadable font: download failed') < 0 &&
        msg
          .text()
          .indexOf(
            'Support for defaultProps will be removed from function components in a future major release'
          ) < 0 &&
        msg.text() !=
          'Failed to load resource: the server responded with a status of 400 (Bad Request)' &&
        !msg.text().includes('/this/does/not/exist.js') &&
        !url.includes('/this/does/not/exist.js') &&
        !url.includes('/api/user/me/') &&
        !url.includes('/api/user/me/token/') &&
        !url.includes('/api/auth/v1/auth/login') &&
        !url.includes('/api/auth/v1/auth/session') &&
        !url.includes('/api/auth/v1/account/authenticators/totp') &&
        !url.includes('/api/auth/v1/account/password/change') &&
        !url.includes('/api/barcode/') &&
        !url.includes('/favicon.ico') &&
        !url.startsWith('https://api.github.com/repos/inventree') &&
        !url.startsWith('https://github.com/inventree/demo-data') &&
        !url.includes('/api/news/') &&
        !url.includes('/api/notifications/') &&
        !url.startsWith('chrome://') &&
        url != 'https://docs.inventree.org/en/versions.json' &&
        url.indexOf('99999') < 0
      )
        messages.push(msg);
    });
    await use(page);
    expect(messages).toEqual([]);
  }
});

export const expect = test.expect;
