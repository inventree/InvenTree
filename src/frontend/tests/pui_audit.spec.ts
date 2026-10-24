import type { Page } from '@playwright/test';
import { expect, test } from './baseFixtures.js';
import { adminuser, allaccessuser, stevenuser } from './defaults.js';
import {
  clearTableSearch,
  loadTab,
  navigate,
  setTableChoiceFilter,
  tableSearch
} from './helpers.js';
import { doCachedLogin } from './login.js';

/**
 * Tests for the audit log (change history) functionality.
 *
 * Note: These tests rely on the audit log entries provided in the demo dataset
 */

// Return the "History" tab on a detail page (if present)
const historyTab = (page: Page) =>
  page
    .getByLabel(/panel-tabs-/)
    .getByRole('tab', { name: 'History', exact: true });

test('Audit - Admin Center', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    user: adminuser,
    url: 'settings/admin/audit-log'
  });

  await page.getByRole('button', { name: 'Audit Log', exact: true }).waitFor();

  // Historical records are displayed
  await tableSearch(page, 'red round table');
  await page.getByRole('cell', { name: 'BOM Item' }).first().waitFor();

  await tableSearch(page, 'PO0020');
  await page.getByRole('cell', { name: 'Purchase Order' }).first().waitFor();
  await page.getByText('UPDATED').first().waitFor();

  // Filter by model type
  await clearTableSearch(page);
  await setTableChoiceFilter(page, 'Model Type', 'Build Order');
  await page.getByRole('cell', { name: 'Build Order' }).first().waitFor();
  await expect(page.getByRole('cell', { name: 'BOM Item' })).toHaveCount(0);

  // Audit log settings
  await page.getByRole('button', { name: 'Audit Log Settings' }).click();
  await page.getByText('Enable Audit Log').waitFor();
  await page.getByText('Delete Old Audit Log Entries').waitFor();
  await page.getByText('Audit Log Deletion Interval').waitFor();
  await page.getByText('Retain Audit Log Summary').waitFor();
});

test('Audit - Detail Pages', async ({ browser }) => {
  // Part (includes BOM item changes)
  const page = await doCachedLogin(browser, {
    user: adminuser,
    url: 'part/111/details'
  });

  await loadTab(page, 'History', true);
  await page
    .getByRole('cell', { name: /to make TB2 \| Test Board 2/ })
    .first()
    .waitFor();
  await page.getByText('Setup Quantity:').first().waitFor();

  // Purchase order (includes line item changes)
  await navigate(page, 'purchasing/purchase-order/9/detail');
  await loadTab(page, 'History', true);

  await page.getByRole('cell', { name: 'PO0009 - PCBWOY' }).first().waitFor();
  await page.getByText('Purchase Order Extra Line').first().waitFor();
  await page.getByText('Supplier Reference:').first().waitFor();
});

test('Audit - Hidden', async ({ browser }) => {
  // Staff user, but the 'DISPLAY_HISTORY_TAB' setting is not enabled
  const page = await doCachedLogin(browser, {
    user: stevenuser,
    url: 'part/111/details'
  });

  await page.getByRole('tab', { name: 'Part Details' }).waitFor();
  await expect(historyTab(page)).toHaveCount(0);

  // Non-staff user
  const page2 = await doCachedLogin(browser, {
    user: allaccessuser,
    url: 'part/111/details'
  });

  await page2.getByRole('tab', { name: 'Part Details' }).waitFor();
  await expect(historyTab(page2)).toHaveCount(0);

  await navigate(page2, 'purchasing/purchase-order/9/detail');
  await page2.getByRole('tab', { name: 'Order Details' }).waitFor();
  await expect(historyTab(page2)).toHaveCount(0);
});
