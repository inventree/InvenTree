import type { Page } from '@playwright/test';

import { createApi } from '../api.js';
import { expect, test } from '../baseFixtures.js';
import { adminuser, readeruser, stevenuser } from '../defaults.js';
import {
  clearTableFilters,
  clickOnRowMenu,
  getRowFromCell,
  loadTab,
  navigate,
  setTableChoiceFilter
} from '../helpers.js';
import { doCachedLogin } from '../login.js';

/*
 * Tests for the "Item Costs" panel on the stock item detail page.
 *
 * Demo data:
 * - Stock item 230 (Green Square Table, quantity 34) has no cost entries
 * - Stock item 220 (1591BTBU, quantity 15) has a single legacy purchase cost of $7.50
 *   (migrated from the old 'purchase_price' field)
 */

// Stock item used to create / edit / delete cost entries
const EDIT_ITEM = 230;

// Stock item with an existing (legacy) cost entry
const VIEW_ITEM = 220;

/**
 * Remove any manual cost entries from the given stock item.
 * Ensures the test starts from a known state (e.g. after a failed attempt)
 */
const removeManualCosts = async (stockItem: number) => {
  const api = await createApi({});

  try {
    const response = await api.get('pricing/stock-cost-entry/', {
      params: { stock_item: stockItem, source: 'manual' }
    });
    expect(response.status(), await response.text()).toBe(200);

    for (const entry of await response.json()) {
      const res = await api.delete(`pricing/stock-cost-entry/${entry.pk}/`);
      expect(res.status(), await res.text()).toBe(204);
    }
  } finally {
    await api.dispose();
  }
};

/**
 * Return the table row for the cost entry with the given notes
 */
const costRow = async (page: Page, notes: string) => {
  return getRowFromCell(page.getByRole('cell', { name: notes, exact: true }));
};

/**
 * Check the "Unit Cost" and "Total Cost" values on the stock item details panel.
 * Pass null to check that the value is not displayed.
 */
const checkCostSummary = async (
  page: Page,
  unitCost: string | null,
  totalCost: string | null
) => {
  await loadTab(page, 'Stock Details');

  for (const [label, value] of [
    ['Unit Cost', unitCost],
    ['Total Cost', totalCost]
  ]) {
    const row = page.getByRole('row').filter({
      has: page.getByRole('cell', { name: label!, exact: true })
    });

    if (value === null) {
      await expect(row).toHaveCount(0);
    } else {
      await expect(row).toContainText(value);
    }
  }
};

test('Stock Costs - Create, Edit, Delete', async ({ browser }) => {
  await removeManualCosts(EDIT_ITEM);

  const page = await doCachedLogin(browser, {
    user: stevenuser,
    url: `stock/item/${EDIT_ITEM}/details`
  });

  await page.getByText('Green Square Table').first().waitFor();

  // No cost data yet
  await checkCostSummary(page, null, null);

  await loadTab(page, 'Item Costs');
  await page.getByText('No records found').waitFor();

  // Create a single (fixed) unit cost
  await page.getByRole('button', { name: 'action-button-add-cost' }).click();
  await page.getByText('Add Item Cost').waitFor();

  // Not an estimate by default - a single "Unit Cost" field is shown
  const estimate = page.getByRole('switch', {
    name: 'boolean-field-estimate'
  });
  await expect(estimate).not.toBeChecked();
  await expect(page.getByLabel('number-field-max_cost')).toHaveCount(0);
  await page
    .getByRole('dialog')
    .getByText('Unit Cost', { exact: true })
    .waitFor();

  await page.getByLabel('choice-field-cost_type').click();
  await page.getByRole('option', { name: 'Fees' }).click();
  await page.getByLabel('number-field-min_cost').fill('2.5');
  await page
    .getByLabel('text-field-notes', { exact: true })
    .fill('Playwright fixed cost');
  await page.getByRole('button', { name: 'Submit' }).click();

  let fixedRow = await costRow(page, 'Playwright fixed cost');
  await expect(fixedRow).toContainText('Fees');
  await expect(fixedRow).toContainText('$2.5');
  await expect(fixedRow).toContainText('manual');
  await expect(fixedRow).toContainText('steven');

  // Create an estimated cost (a range of costs)
  await page.getByRole('button', { name: 'action-button-add-cost' }).click();
  await page.getByText('Add Item Cost').waitFor();
  await expect(estimate).not.toBeChecked();
  await estimate.click();
  await page
    .getByRole('dialog')
    .getByText('Minimum Unit Cost', { exact: true })
    .waitFor();

  await page.getByLabel('choice-field-cost_type').click();
  await page.getByRole('option', { name: 'Landed' }).click();
  await page.getByLabel('number-field-min_cost').fill('1');
  await page.getByLabel('number-field-max_cost').fill('1.5');
  await page
    .getByLabel('text-field-notes', { exact: true })
    .fill('Playwright estimated cost');
  await page.getByRole('button', { name: 'Submit' }).click();

  let estimateRow = await costRow(page, 'Playwright estimated cost');
  await expect(estimateRow).toContainText('Landed');
  await expect(estimateRow).toContainText('$1 - $1.5');

  // The summary is the sum of all cost entries
  await checkCostSummary(page, '$3.5 - $4', '$119 - $136');

  // Filter the table by cost type
  await loadTab(page, 'Item Costs');
  await setTableChoiceFilter(page, 'Cost Type', 'Landed');
  await expect(
    page.getByRole('cell', { name: 'Playwright fixed cost' })
  ).toHaveCount(0);
  await page.getByRole('cell', { name: 'Playwright estimated cost' }).waitFor();
  await clearTableFilters(page);
  await page.getByRole('cell', { name: 'Playwright fixed cost' }).waitFor();

  // Edit the fixed cost - the "estimate" switch is not enabled
  await clickOnRowMenu(
    page.getByRole('cell', { name: 'Playwright fixed cost' })
  );
  await page.getByRole('menuitem', { name: 'Edit' }).click();
  await page.getByText('Edit Item Cost').waitFor();
  await expect(estimate).not.toBeChecked();
  await expect(page.getByLabel('number-field-max_cost')).toHaveCount(0);
  await expect(page.getByLabel('number-field-min_cost')).toHaveValue('2.5');
  await page.getByLabel('number-field-min_cost').fill('3');
  await page.getByRole('button', { name: 'Submit' }).click();

  fixedRow = await costRow(page, 'Playwright fixed cost');
  await expect(fixedRow).toContainText('$3');
  await expect(fixedRow).not.toContainText('$2.5');

  // Edit the estimated cost - the "estimate" switch is enabled
  await clickOnRowMenu(
    page.getByRole('cell', { name: 'Playwright estimated cost' })
  );
  await page.getByRole('menuitem', { name: 'Edit' }).click();
  await page.getByText('Edit Item Cost').waitFor();
  await expect(estimate).toBeChecked();
  await expect(page.getByLabel('number-field-min_cost')).toHaveValue('1');
  await expect(page.getByLabel('number-field-max_cost')).toHaveValue('1.5');

  // Convert it to a fixed cost - the maximum cost is removed
  await estimate.click();
  await expect(page.getByLabel('number-field-max_cost')).toHaveCount(0);
  await page.getByRole('button', { name: 'Submit' }).click();

  estimateRow = await costRow(page, 'Playwright estimated cost');
  await expect(estimateRow).not.toContainText('$1.5');
  await expect(estimateRow).toContainText('$1');

  await checkCostSummary(page, '$4', '$136');

  // Delete both cost entries
  await loadTab(page, 'Item Costs');

  for (const notes of ['Playwright fixed cost', 'Playwright estimated cost']) {
    const cell = page.getByRole('cell', { name: notes });
    await clickOnRowMenu(cell);
    await page.getByRole('menuitem', { name: 'Delete' }).click();
    await page
      .getByText('Are you sure you want to delete this item?')
      .waitFor();
    await page.getByRole('button', { name: 'Delete' }).click();
    await expect(cell).toHaveCount(0);
  }

  await page.getByText('No records found').waitFor();

  // Removing all cost entries removes the cost summary
  await checkCostSummary(page, null, null);
});

test('Stock Costs - View', async ({ browser }) => {
  // The 'reader' user has the 'pricing' view role, but cannot change anything
  const page = await doCachedLogin(browser, {
    user: readeruser,
    url: `stock/item/${VIEW_ITEM}/details`
  });

  await page.getByText('1591BTBU').first().waitFor();

  // Cost summary (single unit cost, multiplied by the quantity of 15)
  await checkCostSummary(page, '$7.5', '$112.5');

  // Legacy cost entry (migrated from the 'purchase_price' field)
  await loadTab(page, 'Item Costs');
  const row = await getRowFromCell(
    page.getByRole('cell', { name: 'legacy', exact: true })
  );
  await expect(row).toContainText('Purchase');
  await expect(row).toContainText('$7.5');

  // Read-only access: no add button or row actions
  await expect(
    page.getByRole('button', { name: 'action-button-add-cost' })
  ).toHaveCount(0);
  await expect(row.getByLabel(/row-action-menu-/i)).toHaveCount(0);

  // Unit cost in the stock item table (optional column)
  await navigate(page, 'stock/location/index/stock-items');
  await page.getByLabel('table-select-columns').click();
  await page.getByRole('menuitem', { name: 'Unit Cost', exact: true }).click();
  await page.keyboard.press('Escape');

  await setTableChoiceFilter(page, 'Has Unit Cost', 'Yes');
  await page
    .locator('table thead th', { hasText: 'Unit Cost' })
    .first()
    .waitFor();
  await page.getByRole('cell', { name: '1591BTBU' }).first().waitFor();

  // Restore the default column selection
  await clearTableFilters(page);
  await page.getByLabel('table-select-columns').click();
  await page.getByRole('menuitem', { name: 'Unit Cost', exact: true }).click();
  await page.keyboard.press('Escape');
});

test('Stock Costs - Audit Log', async ({ browser }) => {
  await removeManualCosts(EDIT_ITEM);

  // Unique notes, to identify the entries created by this test run
  // (audit log entries persist between test runs)
  const suffix = Date.now();
  const notes = `Audit cost ${suffix}`;
  const updatedNotes = `Audit cost ${suffix} (updated)`;

  // The 'admin' user has the 'DISPLAY_HISTORY_TAB' setting enabled
  const page = await doCachedLogin(browser, {
    user: adminuser,
    url: `stock/item/${EDIT_ITEM}/details`
  });

  await page.getByText('Green Square Table').first().waitFor();

  // Create, edit and delete a cost entry via the "Item Costs" table
  await loadTab(page, 'Item Costs');
  await page.getByRole('button', { name: 'action-button-add-cost' }).click();
  await page.getByText('Add Item Cost').waitFor();
  await page.getByLabel('choice-field-cost_type').click();
  await page.getByRole('option', { name: 'Fees' }).click();
  await page.getByLabel('number-field-min_cost').fill('4.25');
  await page.getByLabel('text-field-notes', { exact: true }).fill(notes);
  await page.getByRole('button', { name: 'Submit' }).click();

  await clickOnRowMenu(page.getByRole('cell', { name: notes, exact: true }));
  await page.getByRole('menuitem', { name: 'Edit' }).click();
  await page.getByText('Edit Item Cost').waitFor();
  await page.getByLabel('text-field-notes', { exact: true }).fill(updatedNotes);
  await page.getByRole('button', { name: 'Submit' }).click();

  const cell = page.getByRole('cell', { name: updatedNotes, exact: true });
  await clickOnRowMenu(cell);
  await page.getByRole('menuitem', { name: 'Delete' }).click();
  await page.getByText('Are you sure you want to delete this item?').waitFor();
  await page.getByRole('button', { name: 'Delete' }).click();
  await expect(cell).toHaveCount(0);

  // The changes are recorded in the audit log of the parent stock item
  // (most recent first)
  await loadTab(page, 'History', true);
  await page.getByText(updatedNotes).first().waitFor();

  const rows = page.getByRole('tabpanel').locator('tbody > tr');

  const deleted = rows.nth(0);
  await expect(deleted).toContainText('Deleted');
  await expect(deleted).toContainText('Stock Item Cost Entry');
  await expect(deleted).toContainText('Fees cost (manual)');
  await expect(deleted).toContainText('Object was deleted');

  const updated = rows.nth(1);
  await expect(updated).toContainText('Updated');
  await expect(updated).toContainText('Stock Item Cost Entry');
  await expect(updated).toContainText(notes);
  await expect(updated).toContainText(updatedNotes);

  const created = rows.nth(2);
  await expect(created).toContainText('Created');
  await expect(created).toContainText('Stock Item Cost Entry');
  await expect(created).toContainText('Fees cost (manual)');

  // Changes to related items are hidden when "Include Related" is disabled
  await setTableChoiceFilter(page, 'Include Related', 'No');
  await expect(page.getByText(updatedNotes)).toHaveCount(0);
  await expect(
    page.getByRole('tabpanel').getByText('Stock Item Cost Entry')
  ).toHaveCount(0);
  await clearTableFilters(page);
});
