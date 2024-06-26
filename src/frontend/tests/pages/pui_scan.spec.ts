import { test } from '../baseFixtures';
import { baseUrl } from '../defaults';
import { doQuickLogin } from '../login';

async function defaultScanTest(page, search_text) {
  await doQuickLogin(page);

  await page.goto(`${baseUrl}/scan`);
  await page.getByPlaceholder('Select input method').click();
  await page.getByRole('option', { name: 'Manual input' }).click();
  await page.getByPlaceholder('Enter item serial or data').click();

  // nonsense data
  await page.getByPlaceholder('Enter item serial or data').fill('123');
  await page.getByPlaceholder('Enter item serial or data').press('Enter');
  await page.getByRole('cell', { name: '123' }).click();
  await page.getByRole('cell', { name: 'manually' }).click();
  await page.getByRole('button', { name: 'Lookup part' }).click();
  await page.getByRole('button', { name: 'Delete', exact: true }).click();

  await page.getByPlaceholder('Enter item serial or data').fill(search_text);
  await page.getByPlaceholder('Enter item serial or data').press('Enter');
  await page.getByRole('checkbox').nth(2).check();
  await page.getByRole('button', { name: 'Lookup part' }).click();
}

test('PUI - Pages - Index - Scan (Part)', async ({ page }) => {
  await defaultScanTest(page, '{"part": 1}');

  // part: 1
  await page.getByText('R_10R_0402_1%').waitFor();
  await page.getByText('Stock:').waitFor();
  await page.getByRole('cell', { name: 'part' }).waitFor();
});

test('PUI - Pages - Index - Scan (Stockitem)', async ({ page }) => {
  await defaultScanTest(page, '{"stockitem": 408}');

  // stockitem: 408
  await page.getByText('1551ABK').waitFor();
  await page.getByText('Quantity: 145').waitFor();
  await page.getByRole('cell', { name: 'Quantity: 145' }).waitFor();
});

test('PUI - Pages - Index - Scan (StockLocation)', async ({ page }) => {
  await defaultScanTest(page, '{"stocklocation": 3}');

  // stocklocation: 3
  await page.getByText('Storage Room B', { exact: true }).waitFor();
  await page.getByText('Storage Room B (green door)').waitFor();
  await page.getByRole('cell', { name: 'stocklocation' }).waitFor();
});

test('PUI - Pages - Index - Scan (SupplierPart)', async ({ page }) => {
  await defaultScanTest(page, '{"supplierpart": 204}');

  // supplierpart: 204
  await page.waitForTimeout(1000);
  await page.getByText('1551ABK').first().waitFor();
  await page.getByRole('cell', { name: 'supplierpart' }).waitFor();
});

test('PUI - Pages - Index - Scan (PurchaseOrder)', async ({ page }) => {
  await defaultScanTest(page, '{"purchaseorder": 12}');

  // purchaseorder: 12
  await page.getByText('PO0012').waitFor();
  await page.getByText('Wire from Wirey').waitFor();
  await page.getByRole('cell', { name: 'purchaseorder' }).waitFor();
});

test('PUI - Pages - Index - Scan (SalesOrder)', async ({ page }) => {
  await defaultScanTest(page, '{"salesorder": 6}');

  // salesorder: 6
  await page.getByText('SO0006').waitFor();
  await page.getByText('Selling more stuff to this').waitFor();
  await page.getByRole('cell', { name: 'salesorder' }).waitFor();
});

test('PUI - Pages - Index - Scan (Build)', async ({ page }) => {
  await defaultScanTest(page, '{"build": 8}');

  // build: 8
  await page.getByText('BO0008').waitFor();
  await page.getByText('PCBA build').waitFor();
  await page.getByRole('cell', { name: 'build', exact: true }).waitFor();
});

test('PUI - Pages - Index - Scan (General)', async ({ page }) => {
  await defaultScanTest(page, '{"unknown": 312}');
  await page.getByText('"unknown": 312').waitFor();

  // checkAll
  await page.getByRole('checkbox').nth(0).check();

  // Delete
  await page.getByRole('button', { name: 'Delete', exact: true }).click();

  // Reload to check history is working
  await page.goto(`${baseUrl}/scan`);
  await page.getByText('"unknown": 312').waitFor();

  // Clear history
  await page.getByRole('button', { name: 'Delete History' }).click();
  await page.getByText('No history').waitFor();

  // reload again
  await page.goto(`${baseUrl}/scan`);
  await page.getByText('No history').waitFor();

  // Empty dummy input
  await page.getByPlaceholder('Enter item serial or data').fill('');
  await page.getByPlaceholder('Enter item serial or data').press('Enter');

  // Empty add dummy item
  await page.getByRole('button', { name: 'Add dummy item' }).click();

  // Empty plus sign
  await page
    .locator('div')
    .filter({ hasText: /^InputAdd dummy item$/ })
    .getByRole('button')
    .first()
    .click();

  // Toggle fullscreen
  await page.getByRole('button', { name: 'Toggle Fullscreen' }).click();
  await page.waitForTimeout(1000);
  await page.getByRole('button', { name: 'Toggle Fullscreen' }).click();
  await page.waitForTimeout(1000);
});
