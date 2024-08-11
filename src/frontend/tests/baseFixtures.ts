import { test as baseTest } from '@playwright/test';
import * as crypto from 'crypto';
import * as fs from 'fs';
import os from 'os';
import * as path from 'path';

const istanbulCLIOutput = path.join(process.cwd(), '.nyc_output');
let platform = os.platform();
let systemKeyVar;
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

export const test = baseTest.extend({
  context: async ({ context }, use) => {
    await context.addInitScript(() =>
      window.addEventListener('beforeunload', () =>
        (window as any).collectIstanbulCoverage(
          JSON.stringify((window as any).__coverage__)
        )
      )
    );
    await fs.promises.mkdir(istanbulCLIOutput, { recursive: true });
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
    await use(context);
    for (const page of context.pages()) {
      await page.evaluate(() =>
        (window as any).collectIstanbulCoverage(
          JSON.stringify((window as any).__coverage__)
        )
      );
    }
  },
  // Ensure no errors are thrown in the console
  page: async ({ baseURL, page }, use) => {
    const messages = [];
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
        url != 'http://localhost:8000/api/user/me/' &&
        url != 'http://localhost:8000/api/user/token/' &&
        url != 'http://localhost:8000/api/barcode/' &&
        url != 'https://docs.inventree.org/en/versions.json' &&
        !url.startsWith('http://localhost:8000/api/news/') &&
        !url.startsWith('http://localhost:8000/api/notifications/') &&
        !url.startsWith('chrome://') &&
        url.indexOf('99999') < 0
      )
        messages.push(msg);
    });
    await use(page);
    expect(messages).toEqual([]);
  }
});

export const expect = test.expect;
