import test, { Page, expect } from 'playwright/test';

import { baseUrl } from './defaults.js';
import { doQuickLogin } from './login.js';

const setPluginState = async (
  page: Page,
  pluginName: string,
  state: boolean
) => {
  await page.goto(`${baseUrl}/settings/admin/`);
  await page.getByRole('tab', { name: 'Plugins' }).click();

  // Search for the plugin, to ensure it is visible in the table
  await page.getByPlaceholder('Search').fill(pluginName);
  await page.waitForTimeout(500);

  // Click on the plugin row actions
  await page
    .getByRole('row', { name: pluginName })
    .getByLabel(/row-action-menu-/)
    .click();
  await page.waitForTimeout(500);

  const action: string = state ? 'Activate' : 'Deactivate';
  const success: string = state
    ? 'The plugin was activated'
    : 'The plugin was deactivated';

  const actionButton = await page
    .getByRole('row', { name: pluginName })
    .getByRole('menuitem', { name: action })
    .first();

  if ((await actionButton.count()) > 0) {
    await actionButton.click();
    await page.getByRole('button', { name: 'Submit' }).click();

    await page.getByText(success).waitFor();
  }
};

test('Plugins - Panels', async ({ page }) => {
  await doQuickLogin(page, 'admin', 'inventree');

  // Ensure that the SampleUI plugin is enabled
  await setPluginState(page, 'SampleUI', true);

  // Navigate to the "part" page
  await page.goto(`${baseUrl}/part/69/`);

  // Ensure basic part tab is available
  await page.getByRole('tab', { name: 'Part Details' }).waitFor();

  // Check out each of the plugin panels
  await page.getByRole('tab', { name: 'Sample Panel' }).click();
  await page
    .getByText('This is a sample panel which appears on every page')
    .waitFor();

  await page.getByRole('tab', { name: 'Broken Panel' }).click();
  await page.getByText('Error Loading Plugin').waitFor();

  await page.getByRole('tab', { name: 'Dynamic Part Panel' }).click();
  await page
    .getByText('This panel has been dynamically rendered by the plugin system')
    .waitFor();
  await page.getByText('Instance ID: 69');

  await page.getByRole('tab', { name: 'Part Panel', exact: true }).click();
  await page.getByText('This content has been rendered by a custom plugin');
});
