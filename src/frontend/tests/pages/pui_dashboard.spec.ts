import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';
import { createApi } from '../api.js';
import { test } from '../baseFixtures.js';
import { allaccessuser } from '../defaults.js';
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

  // Enter edit mode and verify widgets can be dragged to new positions
  await page.getByLabel('dashboard-menu').click();
  await page.getByRole('menuitem', { name: 'Edit Layout' }).click();

  const salesItem = page
    .locator('.react-grid-item')
    .filter({ hasText: 'Overdue Sales Orders' });
  const purchaseItem = page
    .locator('.react-grid-item')
    .filter({ hasText: 'Overdue Purchase Orders' });

  const salesBoxBefore = await salesItem.boundingBox();
  const purchaseBoxBefore = await purchaseItem.boundingBox();
  expect(salesBoxBefore).not.toBeNull();
  expect(purchaseBoxBefore).not.toBeNull();

  // Drag the sales widget toward the purchase widget
  await salesItem.dragTo(purchaseItem);
  await page.waitForTimeout(500);

  // At least one of the two widgets should have moved
  const salesBoxAfter = await salesItem.boundingBox();
  const purchaseBoxAfter = await purchaseItem.boundingBox();
  const totalDelta =
    Math.abs((salesBoxAfter?.x ?? 0) - salesBoxBefore!.x) +
    Math.abs((salesBoxAfter?.y ?? 0) - salesBoxBefore!.y) +
    Math.abs((purchaseBoxAfter?.x ?? 0) - purchaseBoxBefore!.x) +
    Math.abs((purchaseBoxAfter?.y ?? 0) - purchaseBoxBefore!.y);
  expect(totalDelta).toBeGreaterThan(10);

  // Drag the purchase widget to the right of the screen
  const purchaseBoxMid = await purchaseItem.boundingBox();
  expect(purchaseBoxMid).not.toBeNull();
  const pStartX = purchaseBoxMid!.x + purchaseBoxMid!.width / 2;
  const pStartY = purchaseBoxMid!.y + purchaseBoxMid!.height / 2;
  await page.mouse.move(pStartX, pStartY);
  await page.mouse.down();
  await page.mouse.move(pStartX + 400, pStartY, { steps: 20 });
  await page.mouse.up();
  await page.waitForTimeout(500);

  const purchaseBoxRight = await purchaseItem.boundingBox();
  expect(purchaseBoxRight!.x).toBeGreaterThan(purchaseBoxMid!.x);

  // Accept the layout before the remove step
  await page.getByLabel('dashboard-accept-layout').click();

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

test('Dashboard - Preserve widget sizes', async ({ browser }) => {
  // Regression: addWidget previously snapped every existing widget back to
  // its minW/minH. Fix is in DashboardLayout.tsx::addWidget (overrideSize=false).
  const TARGET_W = 10;
  const TARGET_H = 6;

  const readLayouts = (page: Page) =>
    page.evaluate(() => {
      const raw = localStorage.getItem('session-settings');
      return raw ? (JSON.parse(raw)?.state?.layouts ?? {}) : {};
    });

  const user = allaccessuser;

  const page = await doCachedLogin(browser, {
    user: user
  });
  await resetDashboard(page);

  // Add widget A; this also persists to the backend user profile.
  await page.getByLabel('dashboard-menu').click();
  await page.getByRole('menuitem', { name: 'Add Widget' }).click();
  await page.getByLabel('dashboard-widgets-filter-input').fill('overdue order');
  await page.getByLabel('add-widget-ovr-so').click();
  await page.getByRole('banner').getByRole('button').click();
  await page.getByText('Overdue Sales Orders').waitFor();
  await page.waitForTimeout(100);

  // Inflate widget A on the backend profile and reload. The auth flow on
  // page load rehydrates layouts from the profile, not localStorage, so a
  // localStorage-only edit would be wiped out on reload.
  const current = await readLayouts(page);
  const inflated: Record<string, any[]> = {};
  for (const bp of Object.keys(current)) {
    inflated[bp] = current[bp].map((it: any) =>
      it?.i === 'ovr-so' ? { ...it, w: TARGET_W, h: TARGET_H } : it
    );
  }

  const api = createApi({
    username: user.username,
    password: user.testcred
  });

  (await api).patch('user/me/profile/', {
    data: {
      widgets: {
        widgets: ['ovr-so'],
        layouts: inflated
      }
    }
  });

  await page.reload();
  await page.getByText('Overdue Sales Orders').waitFor();
  await page.waitForTimeout(100);

  // Sanity: profile rehydration produced the inflated values.
  for (const [bp, items] of Object.entries(await readLayouts(page))) {
    const entry = (items as any[]).find((i) => i?.i === 'ovr-so');

    console.log('entry:', bp, entry);

    expect(entry?.w, `${bp}: ovr-so missing or wrong w`).toBe(TARGET_W);
    expect(entry?.h, `${bp}: ovr-so missing or wrong h`).toBe(TARGET_H);
  }

  // Add widget B. With the bug, this clobbered widget A back to minW/minH.
  await page.getByLabel('dashboard-menu').click();
  await page.getByRole('menuitem', { name: 'Add Widget' }).click();
  await page.getByLabel('dashboard-widgets-filter-input').fill('overdue order');
  await page.getByLabel('add-widget-ovr-po').click();
  await page.getByRole('banner').getByRole('button').click();
  await page.getByText('Overdue Purchase Orders').waitFor();
  await page.waitForTimeout(100);

  for (const [bp, items] of Object.entries(await readLayouts(page))) {
    const entry = (items as any[]).find((i) => i?.i === 'ovr-so');
    expect(entry?.w, `${bp}: ovr-so width was reset`).toBe(TARGET_W);
    expect(entry?.h, `${bp}: ovr-so height was reset`).toBe(TARGET_H);
  }
});
