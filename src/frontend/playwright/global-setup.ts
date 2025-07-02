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

  // Perform login for each user (each in a separate browser instance)
  await doCachedLogin(await chromium.launch(), {
    username: 'admin',
    password: 'inventree'
  });

  await doCachedLogin(await chromium.launch(), {
    username: 'allaccess',
    password: 'nolimits'
  });

  await doCachedLogin(await chromium.launch(), {
    username: 'reader',
    password: 'readonly'
  });

  await doCachedLogin(await chromium.launch(), {
    username: 'steven',
    password: 'wizardstaff'
  });
}

export default globalSetup;
