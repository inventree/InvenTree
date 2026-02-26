import type { Page } from '@playwright/test';
import { test } from '../baseFixtures.js';
import { doCachedLogin } from '../login.js';
import { setPluginState } from '../settings.js';

const resetDashboard = async (page: Page) => {
  await page.getByLabel('dashboard-menu').click();
  await page.getByRole('menuitem', { name: 'Clear Widgets' }).click();
};

test('Dashboard - Basic', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  // Reset dashboard widgets
  await resetDashboard(page);

  await page.getByText('Use the menu to add widgets').waitFor();

  // Let's add some widgets
  await page.getByLabel('dashboard-menu').click();
  await page.getByRole('menuitem', { name: 'Add Widget' }).click();
  await page.getByLabel('dashboard-widgets-filter-input').fill('overdue order');

  await page.getByLabel('add-widget-ovr-so').click();
  await page.getByLabel('add-widget-ovr-po').click();

  await page.getByLabel('dashboard-widgets-filter-clear').click();

  // Close the widget
  await page.getByRole('banner').getByRole('button').click();

  await page.waitForTimeout(500);

  // Check that the widgets are visible
  await page.getByText('Overdue Sales Orders').waitFor();
  await page.getByText('Overdue Purchase Orders').waitFor();

  // Let's remove one of the widgets
  await page.getByLabel('dashboard-menu').click();
  await page.getByRole('menuitem', { name: 'Remove Widgets' }).click();
  await page.getByLabel('remove-dashboard-item-ovr-so').click();

  // Accept the layout
  await page.getByLabel('dashboard-accept-layout').click();
});

test('Dashboard - Stocktake', async ({ browser }) => {
  // Trigger a "stocktake" report from the dashboard

  const page = await doCachedLogin(browser);

  // Reset dashboard widgets
  await resetDashboard(page);

  await page.getByLabel('dashboard-menu').click();
  await page.getByRole('menuitem', { name: 'Add Widget' }).click();
  await page.getByLabel('dashboard-widgets-filter-input').fill('stocktake');
  await page.getByRole('button', { name: 'add-widget-stk' }).click();

  await page.waitForTimeout(100);
  await page.keyboard.press('Escape');

  await page.getByRole('button', { name: 'Generate Stocktake Report' }).click();

  await page.getByText('Select a category to include').waitFor();
  await page.getByRole('button', { name: 'Generate', exact: true }).waitFor();
});

test('Dashboard - Plugins', async ({ browser }) => {
  // Ensure that the "SampleUI" plugin is enabled
  await setPluginState({
    plugin: 'sampleui',
    state: true
  });

  const page = await doCachedLogin(browser);

  await resetDashboard(page);

  // Add a dashboard widget from the SampleUI plugin
  await page.getByLabel('dashboard-menu').click();
  await page.getByRole('menuitem', { name: 'Add Widget' }).click();
  await page.getByLabel('dashboard-widgets-filter-input').fill('sample');

  // Add the widget
  await page.getByLabel(/add-widget-p-sampleui-sample-/).click();

  // Close the widget
  await page.getByRole('banner').getByRole('button').click();

  await page.waitForTimeout(500);

  // Check that the widget is visible
  await page.getByRole('heading', { name: 'Sample Dashboard Item' }).waitFor();
  await page.getByText('Hello world! This is a sample').waitFor();
});
