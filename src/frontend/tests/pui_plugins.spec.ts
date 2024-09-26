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

  // Ensure that the SampleUI plugin is enabled
  await setPluginState({
    request,
    plugin: 'sampleui',
    state: true
  });

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

  // Disable the plugin, and ensure it is no longer visible
  await setPluginState({
    request,
    plugin: 'sampleui',
    state: false
  });
});
