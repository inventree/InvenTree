import test from 'playwright/test';

import { baseUrl } from './defaults.js';
import { doQuickLogin } from './login.js';
import { setPluginState, setSettingState } from './settings.js';

test('Plugins - Panels', async ({ page, request }) => {
  await doQuickLogin(page, 'admin', 'inventree');

  // Ensure that UI plugins are enabled
  await setSettingState({
    request,
    setting: 'ENABLE_PLUGINS_INTERFACE',
    value: true
  });

  await page.waitForTimeout(500);

  // Ensure that the SampleUI plugin is enabled
  await setPluginState({
    request,
    plugin: 'sampleui',
    state: true
  });

  await page.waitForTimeout(500);

  // Navigate to the "part" page
  await page.goto(`${baseUrl}/part/69/`);

  // Ensure basic part tab is available
  await page.getByRole('tab', { name: 'Part Details' }).waitFor();

  // Allow time for the plugin panels to load (they are loaded asynchronously)
  await page.waitForTimeout(1000);

  // Check out each of the plugin panels

  await page.getByRole('tab', { name: 'Broken Panel' }).click();
  await page.waitForTimeout(500);

  await page.getByText('Error occurred while loading plugin content').waitFor();

  await page.getByRole('tab', { name: 'Dynamic Panel' }).click();
  await page.waitForTimeout(500);

  await page.getByText('Instance ID: 69');
  await page
    .getByText('This panel has been dynamically rendered by the plugin system')
    .waitFor();

  await page.getByRole('tab', { name: 'Part Panel', exact: true }).click();
  await page.waitForTimeout(500);
  await page.getByText('This content has been rendered by a custom plugin');

  // Disable the plugin, and ensure it is no longer visible
  await setPluginState({
    request,
    plugin: 'sampleui',
    state: false
  });
});

/**
 * Unit test for custom admin integration for plugins
 */
test('Plugins - Custom Admin', async ({ page, request }) => {
  await doQuickLogin(page, 'admin', 'inventree');

  // Ensure that the SampleUI plugin is enabled
  await setPluginState({
    request,
    plugin: 'sampleui',
    state: true
  });

  // Navigate to the "admin" page
  await page.goto(`${baseUrl}/settings/admin/plugin/`);

  // Open the plugin drawer, and ensure that the custom admin elements are visible
  await page.getByText('SampleUI').click();
  await page.getByRole('button', { name: 'Plugin Information' }).click();
  await page
    .getByLabel('Plugin Detail')
    .getByRole('button', { name: 'Plugin Settings' })
    .click();
  await page.getByRole('button', { name: 'Plugin Configuration' }).click();

  // Check for expected custom elements
  await page
    .getByRole('heading', { name: 'Custom Plugin Configuration Content' })
    .waitFor();
  await page.getByText('apple: banana').waitFor();
  await page.getByText('foo: bar').waitFor();
  await page.getByText('hello: world').waitFor();
});

test('Plugins - Locate Item', async ({ page, request }) => {
  await doQuickLogin(page, 'admin', 'inventree');

  // Ensure that the sample location plugin is enabled
  await setPluginState({
    request,
    plugin: 'samplelocate',
    state: true
  });

  await page.waitForTimeout(500);

  // Navigate to the "stock item" page
  await page.goto(`${baseUrl}/stock/item/287/`);

  // "Locate" this item
  await page.getByLabel('action-button-locate-item').click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Item location requested').waitFor();

  // Show the location
  await page.getByLabel('breadcrumb-1-factory').click();
  await page.waitForTimeout(500);

  await page.getByLabel('action-button-locate-item').click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Item location requested').waitFor();
});
