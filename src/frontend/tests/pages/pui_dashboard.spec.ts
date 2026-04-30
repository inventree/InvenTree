import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';
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

test('Dashboard - Preserve widget sizes when adding new widget', async ({
  browser
}) => {
  // Regression test for a bug where adding a widget from the drawer reset
  // every existing widget on the dashboard back to its minimum width/height.
  //
  // The bug was in DashboardLayout.tsx::addWidget, which called
  // updateLayoutForWidget with overrideSize=true on every existing layout
  // entry. With that flag, w and h are forced to the widget's minW/minH.
  //
  // Strategy: rather than simulating a manual drag-resize (which is flaky
  // and only works in edit mode), we inflate the layout entry of the first
  // widget directly in the persisted store, reload so zustand rehydrates,
  // and then add a second widget via the menu. After adding, we read the
  // store again and assert the first widget retained its enlarged size.
  const TARGET_W = 10;
  const TARGET_H = 6;
  const STORAGE_KEY = 'session-settings';

  const readLayouts = async (page: Page) =>
    page.evaluate((key) => {
      const raw = localStorage.getItem(key);
      if (!raw) return null;
      try {
        return JSON.parse(raw)?.state?.layouts ?? null;
      } catch {
        return null;
      }
    }, STORAGE_KEY);

  const page = await doCachedLogin(browser);
  await resetDashboard(page);

  // Add the first widget so it has a layout entry in the store
  await page.getByLabel('dashboard-menu').click();
  await page.getByRole('menuitem', { name: 'Add Widget' }).click();
  await page.getByLabel('dashboard-widgets-filter-input').fill('overdue order');
  await page.getByLabel('add-widget-ovr-so').click();
  await page.getByRole('banner').getByRole('button').click();
  await page.getByText('Overdue Sales Orders').waitFor();
  await page.waitForTimeout(500);

  // Inflate the layout entry for ovr-so to dimensions well above its
  // minimum (minW=2, minH=1 for QueryCountDashboardWidget). This simulates
  // a user who has resized the widget from its default placement size.
  await page.evaluate(
    ({ key, targetW, targetH }) => {
      const raw = localStorage.getItem(key);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      const layouts = parsed?.state?.layouts;
      if (!layouts) return;
      Object.keys(layouts).forEach((bp) => {
        layouts[bp] = layouts[bp].map((item: any) =>
          item?.i === 'ovr-so' ? { ...item, w: targetW, h: targetH } : item
        );
      });
      localStorage.setItem(key, JSON.stringify(parsed));
    },
    { key: STORAGE_KEY, targetW: TARGET_W, targetH: TARGET_H }
  );

  // Reload so zustand rehydrates the layouts from localStorage
  await page.reload();
  await page.getByText('Overdue Sales Orders').waitFor();
  await page.waitForTimeout(500);

  // Sanity-check that the inflation persisted
  const beforeAdd = await readLayouts(page);
  expect(beforeAdd).not.toBeNull();
  for (const bp of Object.keys(beforeAdd!)) {
    const entry = beforeAdd![bp].find((item: any) => item?.i === 'ovr-so');
    expect(
      entry,
      `pre-add: ovr-so missing from breakpoint ${bp}`
    ).toBeDefined();
    expect(entry.w).toBe(TARGET_W);
    expect(entry.h).toBe(TARGET_H);
  }

  // Add the second widget. Before the fix, this clobbered every existing
  // layout entry's w/h back to its minW/minH.
  await page.getByLabel('dashboard-menu').click();
  await page.getByRole('menuitem', { name: 'Add Widget' }).click();
  await page.getByLabel('dashboard-widgets-filter-input').fill('overdue order');
  await page.getByLabel('add-widget-ovr-po').click();
  await page.getByRole('banner').getByRole('button').click();
  await page.getByText('Overdue Purchase Orders').waitFor();
  await page.waitForTimeout(800);

  // The first widget's layout entry must still have its enlarged
  // dimensions - it must NOT have been reset to minW/minH
  const afterAdd = await readLayouts(page);
  expect(afterAdd).not.toBeNull();
  for (const bp of Object.keys(afterAdd!)) {
    const entry = afterAdd![bp].find((item: any) => item?.i === 'ovr-so');
    expect(
      entry,
      `post-add: ovr-so missing from breakpoint ${bp}`
    ).toBeDefined();
    expect(
      entry.w,
      `breakpoint ${bp}: ovr-so width was reset (got ${entry.w}, expected ${TARGET_W})`
    ).toBe(TARGET_W);
    expect(
      entry.h,
      `breakpoint ${bp}: ovr-so height was reset (got ${entry.h}, expected ${TARGET_H})`
    ).toBe(TARGET_H);
  }
});
