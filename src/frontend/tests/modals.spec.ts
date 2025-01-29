import { test } from './baseFixtures.js';
import { doQuickLogin } from './login.js';

test('Modals - Admin', async ({ page }) => {
  await doQuickLogin(page, 'admin', 'inventree');

  // use server info
  await page.getByLabel('open-spotlight').click();
  await page
    .getByRole('button', {
      name: 'Server Information About this InvenTree instance'
    })
    .click();
  await page.getByRole('cell', { name: 'Instance Name' }).waitFor();
  await page.getByRole('button', { name: 'Close' }).click();

  await page.waitForURL('**/platform/home');

  // use license info
  await page.getByLabel('open-spotlight').click();
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
  await page.getByRole('button', { name: '@sentry/core MIT' }).click();
  await page
    .getByLabel('@sentry/coreMIT')
    .getByText('Copyright (c) 2019')
    .waitFor();

  await page
    .getByLabel('License Information')
    .getByRole('button')
    .first()
    .click();

  // use about
  await page.getByLabel('open-spotlight').click();
  await page
    .getByRole('button', { name: 'About InvenTree About the InvenTree org' })
    .click();
  await page.getByRole('cell', { name: 'InvenTree Version' }).click();
});
