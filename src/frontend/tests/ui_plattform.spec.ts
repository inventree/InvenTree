import { classicUrl } from './baseFixtures';
import { expect, test } from './baseFixtures.js';

test('PUI - Basic test via django', async ({ page }) => {
  await page.goto(`${classicUrl}/platform/`);
  await expect(page).toHaveTitle('InvenTree Demo Server');
  await page.waitForURL('**/platform/');
  await page.getByLabel('username').fill('allaccess');
  await page.getByLabel('password').fill('nolimits');
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform/*');
  await page.goto(`${classicUrl}/platform/`);

  await expect(page).toHaveTitle('InvenTree Demo Server');
});

test('PUI - Basic test', async ({ page }) => {
  await page.goto('./platform/');
  await expect(page).toHaveTitle('InvenTree');
  await page.waitForURL('**/platform/');
  await page.getByLabel('username').fill('allaccess');
  await page.getByLabel('password').fill('nolimits');
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform');
  await page.goto('./platform/');

  await expect(page).toHaveTitle('InvenTree');
});

test('PUI - Pages 1', async ({ page }) => {
  await page.goto('./platform/');
  await expect(page).toHaveTitle('InvenTree');
  await page.waitForURL('**/platform/');
  await page.getByLabel('username').fill('allaccess');
  await page.getByLabel('password').fill('nolimits');
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform');
  await page.goto('./platform/home');

  await page.getByRole('tab', { name: 'Parts' }).click();
  await page.goto('./platform/part/');
  await page.waitForURL('**/platform/part/category/index/details');
  await page.goto('./platform/part/category/index/parts');
  await page.getByText('1551ABK').click();
  await page.getByRole('tab', { name: 'Allocations' }).click();
  await page.getByRole('tab', { name: 'Used In' }).click();
  await page.getByRole('tab', { name: 'Pricing' }).click();
  await page.getByRole('tab', { name: 'Manufacturers' }).click();
  await page.getByRole('tab', { name: 'Suppliers' }).click();
  await page.getByRole('tab', { name: 'Purchase Orders' }).click();
  await page.getByRole('tab', { name: 'Scheduling' }).click();
  await page.getByRole('tab', { name: 'Stocktake' }).click();
  await page.getByRole('tab', { name: 'Related Parts' }).click();
  await page.getByText('1551ACLR').click();
  await page.getByRole('tab', { name: 'Part Details' }).click();
  await page.getByRole('tab', { name: 'Parameters' }).click();
  await page.getByRole('tab', { name: 'Allocations' }).click();
  await page.getByRole('tab', { name: 'Used In' }).click();
  await page.getByRole('tab', { name: 'Pricing' }).click();
  await page.goto('./platform/stock');
  await page.waitForURL('**/platform/stock/location/index/details');
  await page.getByRole('tab', { name: 'Stock Items' }).click();
  await page.getByRole('cell', { name: '1551ABK' }).click();
  await page.getByRole('tab', { name: 'Stock', exact: true }).click();
  await page.getByRole('tab', { name: 'Stock Locations' }).click();
  await page.getByRole('cell', { name: 'Electronics Lab' }).first().click();
  await page.getByRole('tab', { name: 'Default Parts' }).click();
  await page.getByRole('tab', { name: 'Stock Locations' }).click();
  await page.getByRole('tab', { name: 'Stock Items' }).click();
  await page.getByRole('tab', { name: 'Location Details' }).click();
  await page.getByRole('tab', { name: 'Build' }).click();
  await page.getByText('Widget Assembly Variant').click();
  await page.getByRole('tab', { name: 'Allocate Stock' }).click();
  await page.getByRole('tab', { name: 'Incomplete Outputs' }).click();
  await page.getByRole('tab', { name: 'Completed Outputs' }).click();
  await page.getByRole('tab', { name: 'Consumed Stock' }).click();
  await page.getByRole('tab', { name: 'Child Build Orders' }).click();
  await page.getByRole('tab', { name: 'Attachments' }).click();
  await page.getByRole('tab', { name: 'Notes' }).click();
  await page.getByRole('tab', { name: 'Purchasing' }).click();
  await page.getByRole('cell', { name: 'PO0012' }).click();
  await page.getByRole('tab', { name: 'Line Items' }).click();
  await page.getByRole('tab', { name: 'Received Stock' }).click();
  await page.getByRole('tab', { name: 'Attachments' }).click();
  await page.getByRole('tab', { name: 'Purchasing' }).click();
  await page.getByRole('tab', { name: 'Suppliers' }).click();
  await page.getByText('Arrow', { exact: true }).click();
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
  await page.getByLabel('Address title *').click();
  // wait for enabled state
  await page.getByRole('button', { name: 'Submit' }).isEnabled();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByRole('tab', { name: 'Details' }).click();
});

test('PUI - Pages 2', async ({ page }) => {
  await page.goto('./platform/');
  await expect(page).toHaveTitle('InvenTree');
  await page.waitForURL('**/platform/');
  await page.getByLabel('username').fill('admin');
  await page.getByLabel('password').fill('inventree');
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform');

  await page.goto('./platform/sales/');
  await page.waitForURL('**/platform/sales/**');
  await page.waitForURL('**/platform/sales/index/salesorders');
  await page.waitForTimeout(200);
  await page.getByRole('tab', { name: 'Customers' }).click();
  await page.getByText('Customer A').click();
  await page.getByRole('tab', { name: 'Notes' }).click();
  await page.getByRole('tab', { name: 'Attachments' }).click();
  await page.getByRole('tab', { name: 'Contacts' }).click();
  await page.getByRole('tab', { name: 'Assigned Stock' }).click();
  await page.getByRole('tab', { name: 'Return Orders' }).click();
  await page.getByRole('tab', { name: 'Sales Orders' }).click();
  await page.getByRole('tab', { name: 'Contacts' }).click();
  await page.getByRole('cell', { name: 'Dorathy Gross' }).click();
  await page
    .getByRole('row', { name: 'Dorathy Gross 	dorathy.gross@customer.com' })
    .getByRole('button')
    .click();
  await page.waitForTimeout(200);
  await page.getByLabel('Homenav').click();
  await page.getByRole('button', { name: 'System Information' }).click();
  await page.locator('button').filter({ hasText: 'Dismiss' }).click();
  await page.getByRole('link', { name: 'Scanning' }).click();
  await page.locator('.mantine-Overlay-root').click();
  await page.getByPlaceholder('Select input method').click();
  await page.getByRole('option', { name: 'Manual input' }).click();
  await page.getByPlaceholder('Enter item serial or data').click();
  await page.getByPlaceholder('Enter item serial or data').fill('123');
  await page.getByPlaceholder('Enter item serial or data').press('Enter');
  await page.getByRole('cell', { name: 'manually' }).click();
  await page.getByRole('button', { name: 'Lookup part' }).click();
  await page.getByPlaceholder('Select input method').click();
  await page.getByRole('option', { name: 'Manual input' }).click();
});
