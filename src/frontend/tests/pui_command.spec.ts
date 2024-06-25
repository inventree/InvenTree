import { systemKey, test } from './baseFixtures.js';
import { baseUrl } from './defaults.js';
import { doQuickLogin } from './login.js';

test('PUI - Quick Command', async ({ page }) => {
  await doQuickLogin(page);

  // Open Spotlight with Keyboard Shortcut
  await page.locator('body').press(`${systemKey}+k`);
  await page.waitForTimeout(200);
  await page
    .getByRole('button', { name: 'Go to the InvenTree dashboard' })
    .click();
  await page.locator('p').filter({ hasText: 'Dashboard' }).waitFor();
  await page.waitForURL('**/platform/dashboard');

  // Open Spotlight with Button
  await page.getByRole('button', { name: 'Open spotlight' }).click();
  await page.getByRole('button', { name: 'Home Go to the home page' }).click();
  await page
    .getByRole('heading', { name: 'Welcome to your Dashboard,' })
    .click();
  await page.waitForURL('**/platform');

  // Open Spotlight with Keyboard Shortcut and Search
  await page.locator('body').press(`${systemKey}+k`);
  await page.waitForTimeout(200);
  await page.getByPlaceholder('Search...').fill('Dashboard');
  await page.getByPlaceholder('Search...').press('Tab');
  await page.getByPlaceholder('Search...').press('Enter');
  await page.waitForURL('**/platform/dashboard');
});

test('PUI - Quick Command - No Keys', async ({ page }) => {
  await doQuickLogin(page);

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
  await page.getByText('License Information').first().waitFor();
  await page.getByRole('tab', { name: 'backend Packages' }).waitFor();

  await page.getByLabel('License Information').getByRole('button').click();

  // use about
  await page.getByRole('button', { name: 'Open spotlight' }).click();
  await page
    .getByRole('button', { name: 'About InvenTree About the InvenTree org' })
    .click();
  await page.getByText('This information is only').waitFor();

  await page.getByLabel('About InvenTree').getByRole('button').click();

  // use documentation
  await page.getByRole('button', { name: 'Open spotlight' }).click();
  await page
    .getByRole('button', {
      name: 'Documentation Visit the documentation to learn more about InvenTree'
    })
    .click();
  await page.waitForURL('https://docs.inventree.org/**');

  // Test addition of new actions
  await page.goto(`${baseUrl}/playground`);
  await page.locator('p').filter({ hasText: 'Playground' }).waitFor();
  await page.getByRole('button', { name: 'Spotlight actions' }).click();
  await page.getByRole('button', { name: 'Register extra actions' }).click();
  /*
  await page.getByPlaceholder('Search...').fill('secret');
  await page.getByRole('button', { name: 'Secret action It was' }).click();
  await page.getByRole('button', { name: 'Open spotlight' }).click();
  await page.getByPlaceholder('Search...').fill('Another secret action');
  await page
    .getByRole('button', {
      name: 'Another secret action You can register multiple actions with just one command'
    })
    .click();
  await page.getByRole('tab', { name: 'Home' }).click();
  await page.getByRole('button', { name: 'Open spotlight' }).click();
  */
  await page.getByPlaceholder('Search...').fill('secret');
  await page.getByText('Nothing found...').click();
});
