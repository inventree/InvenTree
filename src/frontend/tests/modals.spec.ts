import { test } from './baseFixtures.js';
import { doQuickLogin } from './login.js';

test('PUI - Modals as admin', async ({ page }) => {
  await doQuickLogin(page, 'admin', 'inventree');

  // use server info
  await page.getByRole('button', { name: 'Open spotlight' }).click();
  await page
    .getByRole('button', {
      name: 'Server Information About this Inventree instance'
    })
    .click();
  await page.getByRole('cell', { name: 'Instance Name' }).waitFor();
  await page.getByRole('button', { name: 'Dismiss' }).click();

  await page.waitForURL('**/platform/home');

  // use license info
  await page.getByRole('button', { name: 'Open spotlight' }).click();
  await page
    .getByRole('button', {
      name: 'License Information Licenses for dependencies of the service'
    })
    .click();
  await page.getByText('License Information').first().waitFor();
  await page.getByRole('tab', { name: 'backend Packages' }).click();
  await page.getByRole('button', { name: 'Babel BSD License' }).click();
  await page
    .getByText('by the Babel Team, see AUTHORS for more information')
    .waitFor();

  await page.getByRole('tab', { name: 'frontend Packages' }).click();
  await page.getByRole('button', { name: '@sentry/utils MIT' }).click();
  await page
    .getByLabel('@sentry/utilsMIT')
    .getByText('Copyright (c) 2019 Sentry (')
    .waitFor();

  await page
    .getByLabel('License Information')
    .getByRole('button')
    .first()
    .click();

  // use about
  await page.getByRole('button', { name: 'Open spotlight' }).click();
  await page
    .getByRole('button', { name: 'About InvenTree About the InvenTree org' })
    .click();
  await page.getByRole('cell', { name: 'InvenTree Version' }).click();

  await page.goto('./platform/');

  // qr code modal
  await page.getByRole('button', { name: 'Open QR code scanner' }).click();
  await page.getByRole('banner').getByRole('button').click();
  await page.getByRole('button', { name: 'Open QR code scanner' }).click();
  await page.getByRole('button', { name: 'Close modal' }).click();
  await page.getByRole('button', { name: 'Open QR code scanner' }).click();
  await page.waitForTimeout(500);
  await page.getByRole('banner').getByRole('button').click();
});
