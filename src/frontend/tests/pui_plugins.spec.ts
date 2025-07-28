import test from 'playwright/test';

import {
  clearTableFilters,
  clickOnRowMenu,
  loadTab,
  navigate,
  setTableChoiceFilter
} from './helpers.js';
import { doCachedLogin } from './login.js';
import { setPluginState, setSettingState } from './settings.js';

// Unit test for plugin settings
test('Plugins - Settings', async ({ browser, request }) => {
  const page = await doCachedLogin(browser, {
    username: 'admin',
    password: 'inventree'
  });

  // Ensure that the SampleIntegration plugin is enabled
  await setPluginState({
    request,
    plugin: 'sample',
    state: true
  });

  // Navigate and select the plugin
  await navigate(page, 'settings/admin/plugin/');
  await clearTableFilters(page);
  await page.getByLabel('table-search-input').fill('integration');
  await page.waitForTimeout(250);
  await page.waitForLoadState('networkidle');

  await page
    .getByRole('row', { name: 'SampleIntegrationPlugin' })
    .getByRole('paragraph')
    .click();
  await page.getByRole('button', { name: 'Plugin Information' }).click();
  await page
    .getByLabel('Plugin Detail -')
    .getByRole('button', { name: 'Plugin Settings' })
    .waitFor();

  // Edit numerical value
  await page.getByLabel('edit-setting-NUMERICAL_SETTING').click();
  const originalValue = await page
    .getByLabel('number-field-value')
    .inputValue();

  await page
    .getByLabel('number-field-value')
    .fill(originalValue == '999' ? '1000' : '999');
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.waitForTimeout(500);

  // Change it back
  await page.getByLabel('edit-setting-NUMERICAL_SETTING').click();
  await page.getByLabel('number-field-value').fill(originalValue);
  await page.getByRole('button', { name: 'Submit' }).click();

  // Select supplier
  await page.getByLabel('edit-setting-SELECT_COMPANY').click();
  await page.getByLabel('related-field-value').fill('mouser');
  await page.getByText('Mouser Electronics').click();
});

test('Plugins - User Settings', async ({ browser, request }) => {
  const page = await doCachedLogin(browser);

  // Ensure that the SampleIntegration plugin is enabled
  await setPluginState({
    request,
    plugin: 'sample',
    state: true
  });

  // Navigate to user settings
  await navigate(page, 'settings/user/');
  await loadTab(page, 'Plugin Settings');

  // User settings for the "Sample Plugin" should be visible
  await page.getByRole('button', { name: 'Sample Plugin' }).click();

  await page.getByText('User Setting 1').waitFor();
  await page.getByText('User Setting 2').waitFor();
  await page.getByText('User Setting 3').waitFor();

  // Check for expected setting options
  await page.getByLabel('edit-setting-USER_SETTING_3').click();

  const val = await page.getByLabel('choice-field-value').inputValue();

  await page.getByLabel('choice-field-value').click();

  await page.getByRole('option', { name: 'Choice X' }).waitFor();
  await page.getByRole('option', { name: 'Choice Y' }).waitFor();
  await page.getByRole('option', { name: 'Choice Z' }).waitFor();

  // Change the value of USER_SETTING_3
  await page
    .getByRole('option', { name: val == 'Choice X' ? 'Choice Z' : 'Choice X' })
    .click();
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.getByText('Setting USER_SETTING_3 updated successfully').waitFor();
});

// Test base plugin functionality
test('Plugins - Functionality', async ({ browser }) => {
  // Navigate and select the plugin
  const page = await doCachedLogin(browser, {
    username: 'admin',
    password: 'inventree',
    url: 'settings/admin/plugin/'
  });

  // Filter plugins first
  await clearTableFilters(page);
  await setTableChoiceFilter(page, 'Sample', 'Yes');
  await setTableChoiceFilter(page, 'Builtin', 'No');

  // Activate the plugin
  const cell = await page.getByText('Sample API Caller', { exact: true });
  await clickOnRowMenu(cell);

  // Activate the plugin (unless already activated)
  if ((await page.getByRole('menuitem', { name: 'Deactivate' }).count()) == 0) {
    await page.getByRole('menuitem', { name: 'Activate' }).click();
    await page.getByRole('button', { name: 'Submit' }).click();
    await page.getByText('The plugin was activated').waitFor();
    await page.waitForTimeout(250);
  }

  // Deactivate the plugin again
  await clickOnRowMenu(cell);
  await page.getByRole('menuitem', { name: 'Deactivate' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('The plugin was deactivated').waitFor();

  // Check for custom "mandatory" plugin
  await clearTableFilters(page);
  await setTableChoiceFilter(page, 'Mandatory', 'Yes');
  await setTableChoiceFilter(page, 'Sample', 'Yes');
  await setTableChoiceFilter(page, 'Builtin', 'No');

  await page.getByText('1 - 1 / 1').waitFor();
  await page
    .getByRole('cell', { name: 'SampleLocatePlugin' })
    .first()
    .waitFor();
});

test('Plugins - Panels', async ({ browser, request }) => {
  const page = await doCachedLogin(browser, {
    username: 'admin',
    password: 'inventree'
  });

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
  await navigate(page, 'part/69/');

  // Ensure basic part tab is available
  await loadTab(page, 'Part Details');

  // Allow time for the plugin panels to load (they are loaded asynchronously)
  await page.waitForLoadState('networkidle');

  // Check out each of the plugin panels
  await loadTab(page, 'Broken Panel');
  await page.waitForTimeout(500);

  await page.getByText('Error occurred while loading plugin content').waitFor();

  await loadTab(page, 'Dynamic Panel');
  await page.waitForTimeout(500);

  await page.getByText('Instance ID: 69');
  await page
    .getByText('This panel has been dynamically rendered by the plugin system')
    .waitFor();

  await loadTab(page, 'Part Panel');
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
test('Plugins - Custom Admin', async ({ browser, request }) => {
  const page = await doCachedLogin(browser, {
    username: 'admin',
    password: 'inventree'
  });

  // Ensure that the SampleUI plugin is enabled
  await setPluginState({
    request,
    plugin: 'sampleui',
    state: true
  });

  // Navigate to the "admin" page
  await navigate(page, 'settings/admin/plugin/');

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

test('Plugins - Locate Item', async ({ browser, request }) => {
  const page = await doCachedLogin(browser, {
    username: 'admin',
    password: 'inventree'
  });

  // Ensure that the sample location plugin is enabled
  await setPluginState({
    request,
    plugin: 'samplelocate',
    state: true
  });

  await page.waitForTimeout(500);

  // Navigate to the "stock item" page
  await navigate(page, 'stock/item/287/');
  await page.waitForLoadState('networkidle');

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

test('Plugins - Errors', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    username: 'admin',
    password: 'inventree',
    url: 'settings/admin/plugin/'
  });

  // Reload plugin registry
  await page
    .getByRole('button', { name: 'action-button-reload-plugins' })
    .click();
  await page.getByText('Plugins were reloaded successfully').waitFor();

  // Collapse the "Plugins" accordion
  await page.getByRole('button', { name: 'Plugins', exact: true }).click();
  await page.getByRole('button', { name: 'Plugin Settings' }).waitFor();

  // Expand the "Plugin Errors" accordion
  await page.getByRole('button', { name: 'Plugin Errors' }).click();

  // Check for expected output
  await page
    .getByRole('cell', { name: 'integration.bad_actor' })
    .first()
    .waitFor();
  await page
    .getByText(
      "Plugin 'BadActorPlugin' cannot override final method 'plugin_slug'"
    )
    .first()
    .waitFor();
});
