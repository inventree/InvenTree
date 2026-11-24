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
 * - Stock item 317 (Test Board 2, quantity 6) has a single estimated (range) manufacturing
 *   cost of $33.75 - $67.50
 * - Stock item 331 (Widget Board (assembled), quantity 1) has a single estimated (range)
 *   manufacturing cost of $65 - $130
 * - Stock item 750 (C_10uF_0805, quantity 91) has a legacy purchase cost in AUD, which has
 *   not been converted (no exchange rate), and a "Rework to current revision" cost of $5
 * - Stock items 222 (Wood Screw, quantity 1300), 223 (Wood Screw) and 225 (Blue Paint)
 *   have no cost entries - used for importing costs from a file. Their IDs do not match
 *   any stock item serial number, so the "Stock Item" import column is not ambiguous
 */

// Stock item used to create / edit / delete cost entries
const EDIT_ITEM = 230;

// Stock item with an existing (legacy) cost entry
const VIEW_ITEM = 220;

// Stock items with an existing estimated (range) cost entry
const RANGE_ITEM = 317;
const RANGE_SINGLE_ITEM = 331;

// Stock item with a cost entry which could not be converted to the default currency
const UNCONVERTED_ITEM = 750;

// Stock item used to import costs via the "Item Costs" table (tests/fixtures/stock_costs.csv)
const IMPORT_ITEM = 222;

// Stock items listed in tests/fixtures/stock_costs_admin.csv (imported via the admin center)
const ADMIN_IMPORT_ITEMS = [223, 225];

const LEGACY_NOTES = 'Migrated from stock item purchase price';
const REWORK_NOTES = 'Rework to current revision';

/**
 * Delete the given stock items (cleanup of items created by a test)
 */
const deleteStockItems = async (items: number[]) => {
  const api = await createApi({});

  try {
    for (const pk of items) {
      const res = await api.delete(`stock/${pk}/`);
      expect([204, 404], await res.text()).toContain(res.status());
    }
  } finally {
    await api.dispose();
  }
};

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
  await expect(fixedRow).toContainText('Manual');
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
    page.getByRole('cell', { name: 'Legacy Purchase Price', exact: true })
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

test('Stock Costs - Cost Range', async ({ browser }) => {
  // Existing estimated costs are displayed (and edited) as a range of costs
  const page = await doCachedLogin(browser, {
    user: stevenuser,
    url: `stock/item/${RANGE_ITEM}/details`
  });

  await page.getByText('Test Board 2').first().waitFor();

  // Unit cost range, and total cost range for the quantity of 6
  await checkCostSummary(page, '$33.75 - $67.5', '$202.5 - $405');

  await loadTab(page, 'Item Costs');
  const notes = 'Estimated assembly labour - 0.75 to 1.5 h @ $45/h';
  const row = await costRow(page, notes);
  await expect(row).toContainText('Manufacturing');
  await expect(row).toContainText('$33.75 - $67.5');

  // The edit form shows the "estimate" switch enabled, with both cost fields
  await clickOnRowMenu(page.getByRole('cell', { name: notes, exact: true }));
  await page.getByRole('menuitem', { name: 'Edit' }).click();
  await page.getByText('Edit Item Cost').waitFor();

  await expect(
    page.getByRole('switch', { name: 'boolean-field-estimate' })
  ).toBeChecked();
  await page
    .getByRole('dialog')
    .getByText('Minimum Unit Cost', { exact: true })
    .waitFor();
  await expect(page.getByLabel('number-field-min_cost')).toHaveValue('33.75');
  await expect(page.getByLabel('number-field-max_cost')).toHaveValue('67.5');

  // Close the form without making any changes
  await page.getByRole('button', { name: 'Cancel' }).click();
  await expect(page.getByText('Edit Item Cost')).toHaveCount(0);
  await expect(row).toContainText('$33.75 - $67.5');

  // Single item: unit cost range only (no total cost is displayed)
  await navigate(page, `stock/item/${RANGE_SINGLE_ITEM}/details`);
  await page.getByText('Widget Board (assembled)').first().waitFor();
  await checkCostSummary(page, '$65 - $130', null);
});

test('Stock Costs - Unconverted Costs', async ({ browser }) => {
  // A cost which cannot be converted to the default currency is excluded from the summary
  const page = await doCachedLogin(browser, {
    user: readeruser,
    url: `stock/item/${UNCONVERTED_ITEM}/details`
  });

  await page.getByText('C_10uF_0805').first().waitFor();

  // The summary only includes the converted cost, and is marked as incomplete
  await checkCostSummary(page, '$5', '$455');
  await expect(
    page.getByRole('row').filter({
      has: page.getByRole('cell', { name: 'Unit Cost', exact: true })
    })
  ).toContainText('Incomplete');

  await loadTab(page, 'Item Costs');

  const legacyRow = await costRow(page, LEGACY_NOTES);
  await expect(legacyRow).toContainText('Purchase');
  await expect(legacyRow).toContainText('A$0.5247');
  await expect(legacyRow).toContainText('Not converted');

  const reworkRow = await costRow(page, REWORK_NOTES);
  await expect(reworkRow).toContainText('Other');
  await expect(reworkRow).toContainText('$5');
  await expect(reworkRow).not.toContainText('Not converted');
});

test('Stock Costs - Duplicate', async ({ browser }) => {
  // Duplicating a stock item copies its cost entries (unless disabled)
  const page = await doCachedLogin(browser, {
    user: stevenuser,
    url: `stock/item/${UNCONVERTED_ITEM}/details`
  });

  const created: number[] = [];

  // Duplicate the stock item, and return the pk of the new item
  const duplicate = async (copyCosts: boolean): Promise<number> => {
    await navigate(page, `stock/item/${UNCONVERTED_ITEM}/details`);
    await page.getByText('C_10uF_0805').first().waitFor();

    await page
      .getByRole('button', { name: 'action-menu-stock-item-actions' })
      .click();
    await page
      .getByRole('menuitem', {
        name: 'action-menu-stock-item-actions-duplicate'
      })
      .click();

    // Costs are copied by default
    const copy = page.getByRole('switch', {
      name: 'boolean-field-duplicate.copy_costs'
    });
    await expect(copy).toBeChecked();

    if (!copyCosts) {
      await copy.click();
      await expect(copy).not.toBeChecked();
    }

    await page.getByRole('button', { name: 'Submit' }).click();

    // Wait until we have navigated to the newly created (duplicate) stock item
    await page.waitForURL(
      (url) =>
        /\/stock\/item\/\d+\//.test(url.pathname) &&
        !url.pathname.includes(`/stock/item/${UNCONVERTED_ITEM}/`)
    );

    const pk = Number(page.url().match(/\/stock\/item\/(\d+)\//)![1]);
    created.push(pk);
    await page.waitForLoadState('networkidle');

    return pk;
  };

  try {
    // Copy the costs - the entries (including unconverted entries) are copied verbatim
    await duplicate(true);
    await checkCostSummary(page, '$5', '$455');

    await loadTab(page, 'Item Costs');
    await expect(await costRow(page, LEGACY_NOTES)).toContainText(
      'Not converted'
    );
    await expect(await costRow(page, REWORK_NOTES)).toContainText('$5');

    // Do not copy the costs - the new item has no cost data
    await duplicate(false);
    await checkCostSummary(page, null, null);

    await loadTab(page, 'Item Costs');
    await page.getByText('No records found').waitFor();
  } finally {
    await deleteStockItems(created);
  }
});

/*
 * Disassembly - the form explains how component costs will be recorded.
 *
 * Demo data:
 * - Part 907 (Widget Board (assembled)): pricing data is available for every component
 * - Part 925 (XT90 10-Pack): no pricing data for its components (XT90-M / XT90-F)
 */
test('Stock Costs - Disassembly', async ({ browser }) => {
  const api = await createApi({});

  // Create a new assembly stock item (optionally with a unit cost)
  const createAssembly = async (part: number, unitCost?: number) => {
    const response = await api.post('stock/', {
      data: { part: part, quantity: 2, location: 7 }
    });
    expect(response.status(), await response.text()).toBe(201);

    const result = await response.json();
    const pk: number = (Array.isArray(result) ? result[0] : result).pk;

    if (unitCost !== undefined) {
      const res = await api.post('pricing/stock-cost-entry/', {
        data: { stock_item: pk, cost_type: 10, min_cost: unitCost }
      });
      expect(res.status(), await res.text()).toBe(201);
    }

    return pk;
  };

  const noCost = await createAssembly(925);
  const noPricing = await createAssembly(925, 20);
  const priced = await createAssembly(907, 50);

  const page = await doCachedLogin(browser, {
    user: stevenuser,
    url: `stock/item/${noCost}/details`
  });

  const openDisassembly = async (pk: number) => {
    await navigate(page, `stock/item/${pk}/details`);
    await page
      .getByRole('button', { name: 'action-menu-stock-operations' })
      .click();
    await page
      .getByRole('menuitem', {
        name: 'action-menu-stock-operations-disassemble'
      })
      .click();
    await page.getByText('Disassemble Stock Item').waitFor();
  };

  // Explanation of how component costs will be recorded
  const costInfo = page.getByRole('dialog').getByRole('alert');
  const unitCosts = page.getByRole('textbox', {
    name: 'number-field-unit_cost'
  });

  // 1. No recorded cost - no cost is recorded unless explicitly provided
  await openDisassembly(noCost);
  await expect(costInfo).toContainText('No Cost Will Be Recorded');
  await expect(costInfo).toContainText(
    'This stock item does not have a recorded cost'
  );
  await expect(unitCosts.first()).toHaveAttribute(
    'placeholder',
    'No cost recorded'
  );

  // Explicit costs for every component - nothing to explain
  await unitCosts.nth(0).fill('1.5');
  await unitCosts.nth(1).fill('2');
  await expect(costInfo).toHaveCount(0);
  await page.getByRole('button', { name: 'Cancel' }).click();

  // 2. Missing pricing data - the components are listed
  await openDisassembly(noPricing);
  await expect(costInfo).toContainText('No Cost Will Be Recorded');
  await expect(costInfo).toContainText('Part pricing data is not available');
  await expect(costInfo).toContainText('XT90-M');
  await expect(costInfo).toContainText('XT90-F');

  // An explicit cost for one component - still no cost for the other
  await unitCosts.nth(0).fill('3');
  await expect(costInfo).toContainText('1 component(s) without a unit cost');
  await page.getByRole('button', { name: 'Cancel' }).click();

  // 3. Pricing data for every component - the remaining cost is allocated
  await openDisassembly(priced);
  await expect(costInfo).toContainText('Automatic Cost Allocation');
  await expect(costInfo).toContainText('($100)');
  await expect(unitCosts.first()).toHaveAttribute('placeholder', 'Automatic');

  // An explicit cost (for the first line) reduces the remaining cost
  const firstQuantity = Number(
    await page
      .getByRole('textbox', { name: 'number-field-quantity' })
      .nth(1)
      .inputValue()
  );
  await unitCosts.nth(0).fill('2');
  await expect(costInfo).toContainText(`($${100 - 2 * firstQuantity})`);

  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Stock item disassembled').waitFor();

  // Every component has a "material" cost entry - totalling the cost of the assembly
  const children = await api
    .get('stock/', { params: { parent: priced } })
    .then((res) => res.json());
  expect(children.length).toBeGreaterThan(1);

  let total = 0;

  for (const child of children) {
    const entries = await api
      .get('pricing/stock-cost-entry/', { params: { stock_item: child.pk } })
      .then((res) => res.json());

    expect(entries.length).toBe(1);
    expect(entries[0].source).toBe('disassembly');
    expect(entries[0].cost_type).toBe(40);

    total += Number(entries[0].min_cost) * Number(child.quantity);
  }

  expect(total).toBeCloseTo(100, 2);

  // Remove the stock items created by this test
  const created = [noCost, noPricing, priced, ...children.map((c) => c.pk)];

  for (const pk of created) {
    await api.delete(`stock/${pk}/`);
  }

  await api.dispose();
});

/**
 * Select all rows in the importer, import them, and close the importer
 */
const importAllRows = async (page: Page, count: number) => {
  await page.getByText(`0 / ${count}`).waitFor();

  await page
    .getByRole('row', { name: 'Select all records Row Not' })
    .getByLabel('Select all records')
    .click();
  await page
    .getByRole('button', { name: 'action-button-import-selected' })
    .click();

  await page.getByText('Data has been imported successfully').waitFor();
  await page.getByRole('button', { name: 'Close' }).click();
};

test('Stock Costs - Import', async ({ browser }) => {
  await removeManualCosts(IMPORT_ITEM);

  try {
    const page = await doCachedLogin(browser, {
      user: stevenuser,
      url: `stock/item/${IMPORT_ITEM}/details`
    });

    await checkCostSummary(page, null, null);

    await loadTab(page, 'Item Costs');

    await page
      .getByRole('button', { name: 'action-button-import-costs' })
      .click();

    // The stock item is set automatically - only the file is required
    await page
      .getByRole('dialog', { name: 'Import Item Costs' })
      .locator('input[type="file"]')
      .setInputFiles('./tests/fixtures/stock_costs.csv');
    await page.getByRole('button', { name: 'Submit' }).click();

    await page.getByText('Mapping data columns to database fields').waitFor();

    // The "Stock Item" field is fixed (not mapped from the file)
    await expect(
      page.getByRole('combobox', { name: 'import-column-map-stock_item' })
    ).toHaveCount(0);

    await page.getByRole('button', { name: 'Accept Column Mapping' }).click();

    // Each row is imported against this stock item
    await page.getByText('Imported freight').first().waitFor();
    await page.getByText('Imported handling fee').first().waitFor();
    await page.getByText('Imported rebate').first().waitFor();

    await importAllRows(page, 3);

    // The table is refreshed with the imported entries
    const freight = await costRow(page, 'Imported freight');
    await expect(freight).toContainText('Landed');
    await expect(freight).toContainText('$2.5');
    await expect(freight).toContainText('Manual');
    await expect(freight).toContainText('steven');

    await expect(await costRow(page, 'Imported handling fee')).toContainText(
      '$1 - $1.5'
    );
    await expect(await costRow(page, 'Imported rebate')).toContainText(
      'Adjustment'
    );

    // The unit cost of the stock item includes all the imported entries
    // (2.5 + 1 - 0.5) to (2.5 + 1.5 - 0.5), x 1300 units
    await navigate(page, `stock/item/${IMPORT_ITEM}/details`);
    await checkCostSummary(page, '$3 - $3.5', '$3,900 - $4,550');
  } finally {
    await removeManualCosts(IMPORT_ITEM);
  }
});

test('Stock Costs - Import via Admin Center', async ({ browser }) => {
  for (const item of ADMIN_IMPORT_ITEMS) {
    await removeManualCosts(item);
  }

  try {
    const page = await doCachedLogin(browser, {
      user: stevenuser,
      url: 'settings/admin/import'
    });

    await page
      .getByRole('button', { name: 'action-button-create-import-' })
      .click();

    await page
      .locator('input[type="file"]')
      .setInputFiles('./tests/fixtures/stock_costs_admin.csv');

    await page
      .getByRole('combobox', { name: 'choice-field-model_type' })
      .fill('cost');
    await page
      .getByRole('option', { name: 'Stock Item Cost Entry', exact: true })
      .click();
    await page.getByRole('button', { name: 'Submit' }).click();

    await page.getByText('Mapping data columns to database fields').waitFor();

    // The stock item is read from the file
    await page
      .getByRole('combobox', { name: 'import-column-map-stock_item' })
      .waitFor();

    await page.getByRole('button', { name: 'Accept Column Mapping' }).click();

    await page.getByText('Admin import freight').first().waitFor();
    await page.getByText('Admin import purchase').first().waitFor();

    await importAllRows(page, 2);

    // Confirmation of full import success
    await page.getByRole('cell', { name: '2 / 2' }).first().waitFor();

    // Each cost was imported against the stock item specified in the file
    await navigate(page, `stock/item/${ADMIN_IMPORT_ITEMS[0]}/details`);
    // 0.25 x 1084 units
    await checkCostSummary(page, '$0.25', '$271');

    await navigate(page, `stock/item/${ADMIN_IMPORT_ITEMS[1]}/details`);
    // 12 x 11 units
    await checkCostSummary(page, '$12', '$132');

    await loadTab(page, 'Item Costs');
    const purchase = await costRow(page, 'Admin import purchase');
    await expect(purchase).toContainText('Purchase');
    await expect(purchase).toContainText('Manual');
  } finally {
    for (const item of ADMIN_IMPORT_ITEMS) {
      await removeManualCosts(item);
    }
  }
});
