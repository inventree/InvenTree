import { expect, test } from './baseFixtures.js';
import { user } from './defaults.js';

test('PUI - Stock', async ({ page }) => {
  await page.goto('./platform/');
  await expect(page).toHaveTitle('InvenTree');
  await page.waitForURL('**/platform/');
  await page.getByLabel('username').fill(user.username);
  await page.getByLabel('password').fill(user.password);
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.waitForURL('**/platform');
  await page.goto('./platform/home');
  await page.goto('./platform/stock');
  await page.waitForURL('**/platform/stock/location/index/details');
  await page.waitForTimeout(200);

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
  await page.getByLabel('Address title *').click();
  await page.getByRole('button', { name: 'Submit' }).isEnabled();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByRole('tab', { name: 'Details' }).click();
});
