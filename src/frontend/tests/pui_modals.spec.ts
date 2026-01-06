import { systemKey, test } from './baseFixtures.js';
import { doCachedLogin } from './login.js';
import { setPluginState } from './settings.js';

test('Modals - Admin', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    username: 'admin',
    password: 'inventree'
  });

  // use server info
  await page.getByLabel('open-spotlight').click();
  await page
    .getByRole('button', {
      name: 'Server Information About this InvenTree instance'
    })
    .click();
  await page.getByRole('cell', { name: 'Instance Name' }).waitFor();
  await page.getByRole('button', { name: 'Close' }).click();

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

test('Spotlight - Check Actions', async ({ browser }) => {
  // Enable the UI sample plugin
  await setPluginState({ plugin: 'sampleui', state: true });

  const page = await doCachedLogin(browser);

  await page.waitForLoadState('networkidle');

  // Open Spotlight with Keyboard Shortcut and Search
  await page.locator('body').press(`${systemKey}+k`);
  await page.waitForTimeout(200);
  await page.getByRole('textbox', { name: 'Search...' }).fill('Dashboard');

  await page
    .getByRole('button', { name: 'Dashboard Go to the InvenTree dashboard' })
    .waitFor();

  // User settings
  await page.getByRole('textbox', { name: 'Search...' }).fill('settings');
  await page
    .getByRole('button', { name: 'User Settings Go to your user' })
    .waitFor();

  // Plugin generated action
  await page.getByRole('textbox', { name: 'Search...' }).fill('sample');
  await page.getByRole('button', { name: 'This is a sample action' }).waitFor();
});

test('Spotlight - No Keys', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  await page.waitForLoadState('networkidle');

  // Open Spotlight with Button
  await page.getByLabel('open-spotlight').click();
  await page
    .getByRole('button', { name: 'Dashboard Go to the InvenTree' })
    .click();

  await page.getByText('InvenTree Demo Server - ').waitFor();

  // Use navigation menu
  await page.getByLabel('open-spotlight').click();

  await page.waitForLoadState('networkidle');

  await page.getByRole('button', { name: 'Open Navigation' }).click();

  await page.waitForTimeout(250);

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

  // use license info
  await page.getByLabel('open-spotlight').click();
  await page
    .getByRole('button', {
      name: 'License Information Licenses for dependencies of the service'
    })
    .click();
  await page.getByText('License Information').first().waitFor();
  await page.getByRole('tab', { name: 'backend Packages' }).waitFor();
  await page.getByRole('button', { name: 'Django BSD-3-Clause' }).click();

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
