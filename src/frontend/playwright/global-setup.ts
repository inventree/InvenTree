import type { FullConfig } from '@playwright/test';

import fs from 'node:fs';
import path from 'node:path';

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
}

export default globalSetup;
