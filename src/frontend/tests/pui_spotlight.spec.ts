/**
 * Exercise each of the default "spotlight" navigation actions
 */

import type { Page } from '@playwright/test';
import { test } from './baseFixtures.js';
import { adminuser } from './defaults.js';
import { doCachedLogin } from './login.js';

// Open the spotlight, search for an action, and run it
const runAction = async (page: Page, label: string) => {
  await page.getByLabel('open-spotlight').click();
  await page.getByRole('textbox', { name: 'Search...' }).fill(label);
  await page
    .getByRole('button', { name: new RegExp(`^${label}`) })
    .first()
    .click();
  await page.waitForLoadState('networkidle');
};

test('Spotlight - Navigation Actions', async ({ browser }) => {
  const page = await doCachedLogin(browser, { user: adminuser });

  // Actions which navigate to a new page
  const actions: [string, RegExp][] = [
    ['User Settings', /settings\/user/],
    ['Import Data', /settings\/admin\/import/],
    ['Purchase Orders', /purchasing\/index\/purchaseorders/],
    ['Sales Orders', /sales\/index\/salesorders/],
    ['Transfer Orders', /transfer/],
    ['Return Orders', /sales\/index\/returnorders/],
    ['Build Orders', /manufacturing\/index\/buildorders/],
    ['System Settings', /settings\/system/],
    ['Admin Center', /settings\/admin/],
    ['Error Logs', /settings\/admin\/errors/],
    ['Users', /settings\/admin\/user/],
    ['Plugins', /settings\/admin\/plugin/],
    ['Machines', /settings\/admin\/machine/],
    ['Report Templates', /settings\/admin\/reports/],
    ['Label Templates', /settings\/admin\/labels/]
  ];

  for (const [label, url] of actions) {
    await test.step(label, async () => {
      await runAction(page, label);
      await page.waitForURL(url);
    });
  }

  // Open the barcode scanning modal
  await runAction(page, 'Scan');
  await page.getByPlaceholder('Enter barcode data').waitFor();
  await page.keyboard.press('Escape');

  // Display the list of hotkeys
  await runAction(page, 'Hotkeys');
  await page.getByText('Ctrl').first().waitFor();
  await page.keyboard.press('Escape');

  // Open the navigation menu
  await runAction(page, 'Open Navigation');
  await page.keyboard.press('Escape');
});
