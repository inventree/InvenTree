import { expect, test } from './baseFixtures.js';

test('PUI - Quick Command - no keys', async ({ page }) => {
  await page.goto('./platform/');
  await expect(page).toHaveTitle('InvenTree');
  await page.waitForURL('**/platform/');
  await page.getByLabel('username').fill('allaccess');
  await page.getByLabel('password').fill('nolimits');
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform');

  await expect(page).toHaveTitle('InvenTree');
  await page.waitForURL('**/platform');
  // wait for the page to load - 0.5s
  await page.waitForTimeout(500);

  // Open Spotlight with Button
  await page.getByRole('button', { name: 'Open spotlight' }).click();
  await page.getByRole('button', { name: 'Home Go to the home page' }).click();
  await page
    .getByRole('heading', { name: 'Welcome to your Dashboard,' })
    .click();
  await page.waitForURL('**/platform');

  // Use navigation menu
  await page.getByRole('button', { name: 'Open spotlight' }).click();
  await page
    .getByRole('button', { name: 'Open Navigation Open the main' })
    .click();
  // assert the nav headers are visible
  await page.getByRole('heading', { name: 'Navigation' }).waitFor();
  await page.getByRole('heading', { name: 'Pages' }).waitFor();
  await page.getByRole('heading', { name: 'Documentation' }).waitFor();
  await page.getByRole('heading', { name: 'About' }).waitFor();

  await page.keyboard.press('Escape');

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

  await page.goto('./platform/');

  // use about
  await page.getByRole('button', { name: 'Open spotlight' }).click();
  await page
    .getByRole('button', { name: 'About InvenTree About the InvenTree org' })
    .click();
  await page.getByText('This information is only').waitFor();

  await page.waitForTimeout(500);
  await page.keyboard.press('Escape');
});
