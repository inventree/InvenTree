import { type FullConfig, chromium, request } from '@playwright/test';

import fs from 'node:fs';
import path from 'node:path';
import { apiUrl } from '../tests/defaults';
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

  const baseUrl = config.projects[0].use?.baseURL || 'http://localhost:5173';
  const apiContext = await request.newContext();

  let tries = 10;

  // Wait for the web server to actually be started
  while (tries--) {
    // Perform GET request to the API URL
    console.log('... waiting for API to be available at', apiUrl, '...');
    const response = await apiContext.get(apiUrl, { timeout: 5000 });

    if (response.ok() && response.status() === 200) {
      console.log('... API is available!');
      break;
    }
  }

  // Perform login for each user (each in a separate browser instance)
  await doCachedLogin(await chromium.launch(), {
    username: 'admin',
    password: 'inventree',
    baseUrl: baseUrl
  });

  await doCachedLogin(await chromium.launch(), {
    username: 'allaccess',
    password: 'nolimits',
    baseUrl: baseUrl
  });

  await doCachedLogin(await chromium.launch(), {
    username: 'reader',
    password: 'readonly',
    baseUrl: baseUrl
  });

  await doCachedLogin(await chromium.launch(), {
    username: 'steven',
    password: 'wizardstaff',
    baseUrl: baseUrl
  });
}

export default globalSetup;
