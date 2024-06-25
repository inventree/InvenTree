import { test } from './baseFixtures.js';
import { baseUrl } from './defaults.js';
import { doQuickLogin } from './login.js';

test('PUI - Stock', async ({ page }) => {
  await doQuickLogin(page);

  await page.goto(`${baseUrl}/stock/location/index/`);
  await page.waitForURL('**/platform/stock/location/**');

  await page.getByRole('tab', { name: 'Location Details' }).click();
  await page.waitForURL('**/platform/stock/location/index/details');

  await page.getByRole('tab', { name: 'Stock Items' }).click();
  await page.getByRole('cell', { name: '1551ABK' }).click();

  await page.getByRole('tab', { name: 'Stock', exact: true }).click();
  await page.waitForURL('**/platform/stock/**');
  await page.getByRole('tab', { name: 'Stock Locations' }).click();
  await page.getByRole('cell', { name: 'Electronics Lab' }).first().click();
  await page.getByRole('tab', { name: 'Default Parts' }).click();
  await page.getByRole('tab', { name: 'Stock Locations' }).click();
  await page.getByRole('tab', { name: 'Stock Items' }).click();
  await page.getByRole('tab', { name: 'Location Details' }).click();

  await page.goto(`${baseUrl}/stock/item/1194/details`);
  await page.getByText('D.123 | Doohickey').waitFor();
  await page.getByText('Batch Code: BX-123-2024-2-7').waitFor();
  await page.getByRole('tab', { name: 'Stock Tracking' }).click();
  await page.getByRole('tab', { name: 'Test Data' }).click();
  await page.getByText('395c6d5586e5fb656901d047be27e1f7').waitFor();
  await page.getByRole('tab', { name: 'Installed Items' }).click();
});

test('PUI - Build', async ({ page }) => {
  await doQuickLogin(page);

  await page.getByRole('tab', { name: 'Build' }).click();
  await page.getByText('Widget Assembly Variant').click();
  await page.getByRole('tab', { name: 'Allocate Stock' }).click();
  await page.getByRole('tab', { name: 'Incomplete Outputs' }).click();
  await page.getByRole('tab', { name: 'Completed Outputs' }).click();
  await page.getByRole('tab', { name: 'Consumed Stock' }).click();
  await page.getByRole('tab', { name: 'Child Build Orders' }).click();
  await page.getByRole('tab', { name: 'Attachments' }).click();
  await page.getByRole('tab', { name: 'Notes' }).click();
});

test('PUI - Purchasing', async ({ page }) => {
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

test('PUI - Stock Location Tree', async ({ page }) => {
  await doQuickLogin(page);

  await page.goto(`${baseUrl}/stock/location/index/`);
  await page.waitForURL('**/platform/stock/location/**');
  await page.getByRole('tab', { name: 'Location Details' }).click();

  await page.getByLabel('nav-breadcrumb-action').click();
  await page.getByLabel('nav-tree-toggle-1}').click();
  await page.getByLabel('nav-tree-item-2').click();

  await page.getByLabel('breadcrumb-2-storage-room-a').waitFor();
  await page.getByLabel('breadcrumb-1-factory').click();

  await page.getByRole('cell', { name: 'Factory' }).first().waitFor();
});
