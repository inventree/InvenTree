import { type FullConfig, chromium } from '@playwright/test';

import fs from 'node:fs';
import path from 'node:path';
import { doCachedLogin } from '../tests/login';

async function globalSetup(config: FullConfig) {
  const authDir = path.resolve('./playwright/auth');

  if (fs.existsSync(authDir)) {
    // Clear out the cached authentication states
    fs.rm(path.resolve('./playwright/auth'), { recursive: true }, (err) => {
      if (err) {
        console.error('Failed to clear out cached authentication states:', err);
      } else {
        console.log('Removed cached authentication states');
      }
    });
  }

  // Perform login for each user
  const browser = await chromium.launch();

  await doCachedLogin(browser, {
    username: 'admin',
    password: 'inventree'
  });

  await doCachedLogin(browser, {
    username: 'allaccess',
    password: 'nolimits'
  });

  await doCachedLogin(browser, {
    username: 'reader',
    password: 'readonly'
  });

  await doCachedLogin(browser, {
    username: 'steven',
    password: 'wizardstaff'
  });
}

export default globalSetup;
