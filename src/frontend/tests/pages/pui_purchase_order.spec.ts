import { test } from '../baseFixtures.ts';
import { baseUrl } from '../defaults.ts';
import { clickButtonIfVisible, openFilterDrawer } from '../helpers.ts';
import { doQuickLogin } from '../login.ts';

test('Purchase Orders - General', async ({ page }) => {
  await doQuickLogin(page);

  await page.getByRole('tab', { name: 'Purchasing' }).click();
  await page.getByRole('cell', { name: 'PO0012' }).click();
  await page.waitForTimeout(200);

  await page.getByRole('tab', { name: 'Line Items' }).click();
  await page.getByRole('tab', { name: 'Received Stock' }).click();
  await page.getByRole('tab', { name: 'Attachments' }).click();
  await page.getByRole('tab', { name: 'Purchasing' }).click();
  await page.getByRole('tab', { name: 'Suppliers' }).click();
  await page.getByText('Arrow', { exact: true }).click();
  await page.waitForTimeout(200);

  await page.getByRole('tab', { name: 'Supplied Parts' }).click();
  await page.getByRole('tab', { name: 'Purchase Orders' }).click();
  await page.getByRole('tab', { name: 'Stock Items' }).click();
  await page.getByRole('tab', { name: 'Contacts' }).click();
  await page.getByRole('tab', { name: 'Addresses' }).click();
  await page.getByRole('tab', { name: 'Attachments' }).click();
  await page.getByRole('tab', { name: 'Purchasing' }).click();
  await page.getByRole('tab', { name: 'Manufacturers' }).click();
  await page.getByText('AVX Corporation').click();
  await page.waitForTimeout(200);

  await page.getByRole('tab', { name: 'Addresses' }).click();
  await page.getByRole('cell', { name: 'West Branch' }).click();
  await page.locator('.mantine-ScrollArea-root').click();
  await page
    .getByRole('row', { name: 'West Branch Yes Surf Avenue 9' })
    .getByRole('button')
    .click();
  await page.getByRole('menuitem', { name: 'Edit' }).click();

  await page.getByLabel('text-field-title').waitFor();
  await page.getByLabel('text-field-line2').waitFor();

  // Read the current value of the cell, to ensure we always *change* it!
  const value = await page.getByLabel('text-field-line2').inputValue();
  await page
    .getByLabel('text-field-line2')
    .fill(value == 'old' ? 'new' : 'old');

  await page.getByRole('button', { name: 'Submit' }).isEnabled();

  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByRole('tab', { name: 'Details' }).waitFor();
});

test('Purchase Orders - Filters', async ({ page }) => {
  await doQuickLogin(page, 'reader', 'readonly');

  await page.getByRole('tab', { name: 'Purchasing' }).click();
  await page.getByRole('tab', { name: 'Purchase Orders' }).click();

  // Open filters drawer
  await openFilterDrawer(page);
  await clickButtonIfVisible(page, 'Clear Filters');

  await page.getByRole('button', { name: 'Add Filter' }).click();

  // Check for expected filter options
  await page.getByPlaceholder('Select filter').fill('before');
  await page.getByRole('option', { name: 'Created Before' }).waitFor();
  await page.getByRole('option', { name: 'Completed Before' }).waitFor();
  await page.getByRole('option', { name: 'Target Date Before' }).waitFor();

  await page.getByPlaceholder('Select filter').fill('after');
  await page.getByRole('option', { name: 'Created After' }).waitFor();
  await page.getByRole('option', { name: 'Completed After' }).waitFor();
  await page.getByRole('option', { name: 'Target Date After' }).waitFor();
});

test('Purchase Orders - Order Parts', async ({ page }) => {
  await doQuickLogin(page);

  // Open "Order Parts" wizard from the "parts" table
  await page.getByRole('tab', { name: 'Parts' }).click();
  await page
    .getByLabel('panel-tabs-partcategory')
    .getByRole('tab', { name: 'Parts' })
    .click();

  // Select multiple parts
  for (let ii = 1; ii < 5; ii++) {
    await page.getByLabel(`Select record ${ii}`, { exact: true }).click();
  }

  await page.getByLabel('action-menu-part-actions').click();
  await page.getByLabel('action-menu-part-actions-order-parts').click();
  await page
    .getByRole('heading', { name: 'Order Parts' })
    .locator('div')
    .first()
    .waitFor();
  await page.getByRole('banner').getByRole('button').click();

  // Open "Order Parts" wizard from the "Stock Items" table
  await page.getByRole('tab', { name: 'Stock' }).click();
  await page.getByRole('tab', { name: 'Stock Items' }).click();

  // Select multiple stock items
  for (let ii = 2; ii < 7; ii += 2) {
    await page.getByLabel(`Select record ${ii}`, { exact: true }).click();
  }

  await page
    .getByLabel('Stock Items')
    .getByLabel('action-menu-stock-actions')
    .click();
  await page.getByLabel('action-menu-stock-actions-order-stock').click();
  await page.getByRole('banner').getByRole('button').click();

  // Order from the part detail page
  await page.goto(`${baseUrl}/part/69/`);
  await page.waitForURL('**/part/69/**');

  await page.getByLabel('action-menu-stock-actions').click();
  await page.getByLabel('action-menu-stock-actions-order').click();

  // Select supplier part
  await page.getByLabel('related-field-supplier_part').click();
  await page.getByText('WM1731-ND').click();

  // Option to create a new supplier part
  await page.getByLabel('action-button-new-supplier-part').click();
  await page.getByLabel('related-field-supplier', { exact: true }).click();
  await page.getByText('Future').click();
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Select purchase order
  await page.getByLabel('related-field-purchase_order').click();
  await page.getByText('PO0001').click();

  // Option to create a new purchase order
  await page.getByLabel('action-button-new-purchase-order').click();
  await page.getByLabel('related-field-project_code').click();
  await page.getByText('PRJ-PHO').click();
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Add the part to the purchase order
  await page.getByLabel('action-button-add-to-selected').click();
  await page.getByLabel('number-field-quantity').fill('100');
  await page.waitForTimeout(250);
  await page.getByRole('button', { name: 'Submit' }).click();
  await page
    .getByText('All selected parts added to a purchase order')
    .waitFor();
});

/**
 * Tests for receiving items against a purchase order
 */
test('Purchase Orders - Receive Items', async ({ page }) => {
  await doQuickLogin(page);

  await page.getByRole('tab', { name: 'Purchasing' }).click();
  await page.getByRole('cell', { name: 'PO0014' }).click();

  await page.getByRole('tab', { name: 'Order Details' }).click();
  await page.getByText('0 / 3').waitFor();

  // Select all line items to receive
  await page.getByRole('tab', { name: 'Line Items' }).click();

  await page.getByLabel('Select all records').click();
  await page.waitForTimeout(200);
  await page.getByLabel('action-button-receive-items').click();

  // Check for display of individual locations
  await page
    .getByRole('cell', { name: /Choose Location/ })
    .getByText('Parts Bins')
    .waitFor();
  await page
    .getByRole('cell', { name: /Choose Location/ })
    .getByText('Room 101')
    .waitFor();
  await page.getByText('Mechanical Lab').waitFor();

  await page.getByRole('button', { name: 'Cancel' }).click();
});
