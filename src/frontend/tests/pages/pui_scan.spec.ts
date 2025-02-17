import { test } from '../baseFixtures';
import { navigate } from '../helpers';
import { doQuickLogin } from '../login';

const scan = async (page, barcode) => {
  await page.getByLabel('barcode-input-scanner').click();
  await page.getByLabel('barcode-scan-keyboard-input').fill(barcode);
  await page.getByRole('button', { name: 'Scan', exact: true }).click();
};

test('Scanning - Dialog', async ({ page }) => {
  await doQuickLogin(page);

  await page.getByRole('button', { name: 'Open Barcode Scanner' }).click();
  await scan(page, '{"part": 15}');

  await page.getByText('Part: R_550R_0805_1%', { exact: true }).waitFor();
  await page.getByText('Available:').waitFor();
  await page.getByText('Required:').waitFor();
});

test('Scanning - Basic', async ({ page }) => {
  await doQuickLogin(page);

  // Navigate to the 'scan' page
  await page.getByLabel('navigation-menu').click();
  await page.getByRole('button', { name: 'Scan Barcode' }).click();

  await page.getByText('Scan or enter barcode data').waitFor();

  // Select the scanner input
  await page.getByLabel('barcode-input-scanner').click();
  await page.getByPlaceholder('Enter barcode data').fill('123-abc');
  await page.getByRole('button', { name: 'Scan', exact: true }).click();

  // Select the camera input
  await page.getByLabel('barcode-input-camera').click();
  await page.getByText('Start scanning by selecting a camera').waitFor();

  await page.getByText('No match found for barcode').waitFor();
});

test('Scanning - Part', async ({ page }) => {
  await doQuickLogin(page);
  await navigate(page, 'scan/');

  await scan(page, '{"part": 1}');

  await page.getByText('R_10R_0402_1%').waitFor();
  await page.getByText('Stock:').waitFor();
  await page.getByRole('cell', { name: 'part', exact: true }).waitFor();
});

test('Scanning - Stockitem', async ({ page }) => {
  await doQuickLogin(page);
  await navigate(page, 'scan/');
  await scan(page, '{"stockitem": 408}');

  await page.getByText('1551ABK').waitFor();
  await page.getByText('Quantity: 100').waitFor();
  await page.getByRole('cell', { name: 'Quantity: 100' }).waitFor();
});

test('Scanning - StockLocation', async ({ page }) => {
  await doQuickLogin(page);
  await navigate(page, 'scan/');
  await scan(page, '{"stocklocation": 3}');

  // stocklocation: 3
  await page.getByText('Factory/Storage Room B', { exact: true }).waitFor();
  await page.getByText('Storage Room B (green door)').waitFor();
  await page
    .getByRole('cell', { name: 'stocklocation', exact: true })
    .waitFor();
});

test('Scanning - SupplierPart', async ({ page }) => {
  await doQuickLogin(page);
  await navigate(page, 'scan/');
  await scan(page, '{"supplierpart": 204}');

  // supplierpart: 204
  await page.waitForTimeout(1000);
  await page.getByText('1551ABK').first().waitFor();
  await page.getByRole('cell', { name: 'supplierpart', exact: true }).waitFor();
});

test('Scanning - PurchaseOrder', async ({ page }) => {
  await doQuickLogin(page);
  await navigate(page, 'scan/');
  await scan(page, '{"purchaseorder": 12}');

  // purchaseorder: 12
  await page.getByText('PO0012').waitFor();
  await page.getByText('Wire from Wirey').waitFor();
  await page
    .getByRole('cell', { name: 'purchaseorder', exact: true })
    .waitFor();
});

test('Scanning - SalesOrder', async ({ page }) => {
  await doQuickLogin(page);
  await navigate(page, 'scan/');
  await scan(page, '{"salesorder": 6}');

  // salesorder: 6
  await page.getByText('SO0006').waitFor();
  await page.getByText('Selling more stuff to this').waitFor();
  await page.getByRole('cell', { name: 'salesorder', exact: true }).waitFor();
});

test('Scanning - Build', async ({ page }) => {
  await doQuickLogin(page);
  await navigate(page, 'scan/');
  await scan(page, '{"build": 8}');

  // build: 8
  await page.getByText('BO0008').waitFor();
  await page.getByText('PCBA build').waitFor();
  await page.getByRole('cell', { name: 'build', exact: true }).waitFor();
});
