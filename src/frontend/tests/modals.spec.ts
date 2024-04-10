import { expect, test } from './baseFixtures.js';

test('PUI - Modals as admin', async ({ page }) => {
  await page.goto('./platform/');
  await expect(page).toHaveTitle('InvenTree');
  await page.waitForURL('**/platform/');
  await page.getByLabel('username').fill('admin');
  await page.getByLabel('password').fill('inventree');
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform');

  // use server info
  await page.getByRole('button', { name: 'Open spotlight' }).click();
  await page
    .getByRole('button', {
      name: 'Server Information About this Inventree instance'
    })
    .click();
  await page.getByRole('cell', { name: 'Instance Name' }).waitFor();
  await page.getByRole('button', { name: 'Dismiss' }).click();

  await page.waitForURL('**/platform');

  // use license info
  await page.getByRole('button', { name: 'Open spotlight' }).click();
  await page
    .getByRole('button', {
      name: 'License Information Licenses for dependencies of the service'
    })
    .click();
  await page.getByText('License Information').first().waitFor();
  await page.getByRole('tab', { name: 'backend Packages' }).waitFor();

  await page.getByLabel('License Information').getByRole('button').click();

  // use about
  await page.getByRole('button', { name: 'Open spotlight' }).click();
  await page
    .getByRole('button', { name: 'About InvenTree About the InvenTree org' })
    .click();
  await page.getByRole('cell', { name: 'InvenTree Version' }).click();

  await page.goto('./platform/');
});
