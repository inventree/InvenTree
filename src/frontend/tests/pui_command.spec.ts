import { systemKey, test } from './baseFixtures.js';
import { doQuickLogin } from './login.js';

test('Quick Command', async ({ page }) => {
  await doQuickLogin(page);

  // Open Spotlight with Keyboard Shortcut and Search
  await page.locator('body').press(`${systemKey}+k`);
  await page.waitForTimeout(200);
  await page.getByPlaceholder('Search...').fill('Dashboard');
  await page.getByPlaceholder('Search...').press('Tab');
  await page.getByPlaceholder('Search...').press('Enter');
  await page.waitForURL('**/platform/home');
});

test('Quick Command - No Keys', async ({ page }) => {
  await doQuickLogin(page);

  // Open Spotlight with Button
  await page.getByLabel('open-spotlight').click();
  await page
    .getByRole('button', { name: 'Dashboard Go to the InvenTree' })
    .click();

  await page.getByText('InvenTree Demo Server - ').waitFor();
  await page.waitForURL('**/platform/home');

  // Use navigation menu
  await page.getByLabel('open-spotlight').click();
  await page
    .getByRole('button', { name: 'Open Navigation Open the main' })
    .click();

  await page.waitForTimeout(1000);

  // assert the nav headers are visible
  await page.getByText('Navigation').waitFor();
  await page.getByText('Documentation').waitFor();
  await page.getByText('About').first().waitFor();
  await page
    .getByRole('button', { name: 'Notifications', exact: true })
    .waitFor();
  await page.getByRole('button', { name: 'Dashboard', exact: true }).waitFor();

  // close the nav
  await page.keyboard.press('Escape');

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
  await page.getByRole('tab', { name: 'backend Packages' }).waitFor();
  await page.getByRole('button', { name: 'Django BSD License' }).click();

  await page.keyboard.press('Escape');

  // use about
  await page.getByLabel('open-spotlight').click();
  await page
    .getByRole('button', { name: 'About InvenTree About the InvenTree org' })
    .click();
  await page.getByText('This information is only').waitFor();

  await page.getByLabel('About InvenTree').getByRole('button').click();

  // use documentation
  await page.getByLabel('open-spotlight').click();
  await page
    .getByRole('button', {
      name: 'Documentation Visit the documentation to learn more about InvenTree'
    })
    .click();
  await page.waitForURL('https://docs.inventree.org/**');

  // TODO: Test addition of new actions
});
