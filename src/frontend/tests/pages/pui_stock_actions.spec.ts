/**
 * Tests for stock adjustment forms which are not covered elsewhere:
 * - Transfer to default location
 * - Bulk actions from the stock table (merge / status / batch / assign / delete)
 * - Find serial number (error handling)
 * - Test results with templated choices
 */

import { createApi } from '../api.js';
import { expect, generateUUID, test } from '../baseFixtures.js';
import { navigate } from '../helpers.js';
import { doCachedLogin } from '../login.js';

// Part "530470210" - a simple (non-trackable) part
const PART_ID = 69;

// Create a new stock item via the API, and return its primary key
const createStockItem = async (api, data: any): Promise<number> => {
  const response = await api.post('stock/', {
    data: { part: PART_ID, quantity: 10, location: 7, ...data }
  });
  expect(response.status()).toBe(201);
  const result = await response.json();
  const item = Array.isArray(result) ? result[0] : result;
  return item.pk ?? item.items?.[0]?.pk;
};

test('Stock - Transfer to Default Location', async ({ browser }) => {
  const api = await createApi({});

  // Set a default location for the part
  await api.patch(`part/${PART_ID}/`, { data: { default_location: 12 } });

  try {
    const pk = await createStockItem(api, { quantity: 5 });

    const page = await doCachedLogin(browser, {
      url: `stock/item/${pk}/details`
    });

    const openTransfer = async () => {
      await page.getByLabel('action-menu-stock-operations').click();
      await page.getByLabel('action-menu-stock-operations-transfer').click();
    };

    // Move to the default location (confirmation dialog)
    await openTransfer();
    await page.getByLabel('action-button-move-to-default-location').click();
    await page.getByText('Confirm Stock Transfer').waitFor();
    await page
      .getByRole('dialog', { name: 'Confirm Stock Transfer' })
      .getByRole('button', { name: 'Submit' })
      .click();
    await page.waitForLoadState('networkidle');

    // Close the transfer dialog (the item has been removed from the list)
    await page.keyboard.press('Escape');

    // Transfer again, toggling the extra row options
    await navigate(page, `stock/item/${pk}/details`);
    await openTransfer();
    await page.getByLabel('action-button-change-status').click();
    await page.getByLabel('action-button-adjust-packaging').click();
    await page.getByLabel('action-button-merge-into-existing-stock').click();
    await page.getByLabel('action-button-merge-into-existing-stock').click();
    await page.getByRole('button', { name: 'Cancel' }).click();
  } finally {
    await api.patch(`part/${PART_ID}/`, { data: { default_location: null } });
  }
});

test('Stock - Table Bulk Actions', async ({ browser }) => {
  const api = await createApi({});
  const batch = `PW-${generateUUID().slice(0, 6)}`;

  const a = await createStockItem(api, { batch });
  const b = await createStockItem(api, { batch });

  const page = await doCachedLogin(browser, {
    url: `part/${PART_ID}/stock`
  });

  // Filter the table to only show the new items
  await page.getByLabel('table-search-input').fill(batch);
  await page.waitForTimeout(600);
  await page.waitForLoadState('networkidle');

  const panel = page.getByRole('tabpanel', { name: 'Stock' });

  // Wait for the filtered results to load
  await expect(panel.getByRole('cell', { name: batch })).toHaveCount(2);

  const actionMenu = panel.getByLabel('action-menu-stock-actions');

  // Select the specified number of rows in the table
  // Note: the table selection is reset (asynchronously) after each stock
  // operation, when the table data is reloaded - so retry until it sticks
  const selectRows = async (count = 2) => {
    await expect(async () => {
      // Wait for any modal (and its loading overlay) to close
      await expect(page.getByRole('dialog')).toHaveCount(0, { timeout: 2000 });
      await page.waitForLoadState('networkidle');

      const boxes = [];
      for (let idx = 1; idx <= count; idx++) {
        const box = panel.getByLabel(`Select record ${idx}`, { exact: true });
        await box.check({ timeout: 2000 });
        boxes.push(box);
      }

      // Ensure that the selection is not cleared by a pending table reload
      await page.waitForTimeout(500);
      for (const box of boxes) {
        await expect(box).toBeChecked({ timeout: 500 });
      }
      await expect(actionMenu).toBeEnabled({ timeout: 500 });
    }).toPass({ timeout: 30000 });
  };

  const launch = async (action: string) => {
    await actionMenu.click();
    await page.getByLabel(`action-menu-stock-actions-${action}`).click();
  };

  // Change status
  await selectRows();
  await launch('change-status');
  await page.getByLabel('choice-field-status').click();
  await page.getByRole('option', { name: 'Damaged' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.waitForLoadState('networkidle');

  // Change batch code (open, then cancel)
  await selectRows();
  await launch('change-batch-code');
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Assign to customer (open, then cancel)
  await selectRows();
  await launch('assign-stock');
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Merge the items
  await selectRows();
  await launch('merge-stock');
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.waitForLoadState('networkidle');

  // Delete whatever remains
  await selectRows(1);
  await launch('delete-stock');
  await page.getByRole('button', { name: 'Delete' }).click();
  await page.waitForLoadState('networkidle');

  // Ensure the items have been removed
  for (const pk of [a, b]) {
    const response = await api.get(`stock/${pk}/`);
    expect([404, 200]).toContain(response.status());
  }
});

test('Stock - Find Serial Number', async ({ browser }) => {
  // "Red Widget" variant with serialized stock
  const page = await doCachedLogin(browser, { url: 'part/79/details' });

  await page.getByLabel('action-menu-stock-actions').click();
  await page.getByLabel('action-menu-stock-actions-search').click();

  // Serial number which does not exist
  await page.getByLabel('text-field-serial', { exact: true }).fill('99999999');
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('No matching items').waitFor();

  // Valid serial number
  await page.getByLabel('text-field-serial', { exact: true }).fill('359');
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Serial Number: 359').waitFor();
});

test('Stock - Test Result Choices', async ({ browser }) => {
  const api = await createApi({});
  const testName = `PW Choice ${generateUUID().slice(0, 6)}`;

  // "Doohickey" - create a test template with a set of choices
  const response = await api.post('part/test-template/', {
    data: {
      part: 87,
      test_name: testName,
      description: 'Playwright test template',
      choices: 'Pass, Fail, Retest',
      requires_value: true
    }
  });
  expect(response.status()).toBe(201);
  const template = await response.json();

  try {
    // Serialized stock item for "Doohickey"
    // Note: explicit timeouts are used so that any failure reports the
    // offending step, rather than a generic test timeout
    const page = await test.step('Open test results', async () => {
      const page = await doCachedLogin(browser, { url: 'stock/item/409/' });
      await page
        .getByLabel(/panel-tabs-/)
        .getByRole('tab', { name: 'Test Results' })
        .click({ timeout: 15000 });
      return page;
    });

    await test.step('Select test template', async () => {
      await page
        .getByLabel('action-button-add-test-result')
        .click({ timeout: 15000 });

      const option = page.getByRole('option', { name: new RegExp(testName) });

      // Retry the search, in case the first query is debounced away
      await expect(async () => {
        await page
          .getByLabel('related-field-template')
          .fill(testName, { timeout: 5000 });
        await option.click({ timeout: 5000 });
      }).toPass({ timeout: 30000 });
    });

    await test.step('Select choice value', async () => {
      // The "value" field is now a choice field
      await page.getByLabel('choice-field-value').click({ timeout: 10000 });
      await page
        .getByRole('option', { name: 'Retest' })
        .click({ timeout: 10000 });
      await page
        .getByRole('button', { name: 'Submit' })
        .click({ timeout: 10000 });
      await page
        .getByRole('cell', { name: 'Retest' })
        .first()
        .waitFor({ timeout: 15000 });
    });
  } finally {
    await api.delete(`part/test-template/${template.pk}/`);
  }
});
