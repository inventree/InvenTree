import type { Page } from '@playwright/test';
import { createApi } from '../api';
import { test } from '../baseFixtures';
import { doCachedLogin } from '../login';

const scan = async (page: Page, barcode: string) => {
  await page.getByLabel('barcode-input-scanner').click();
  await page.getByLabel('barcode-scan-keyboard-input').fill(barcode);
  await page.getByRole('button', { name: 'Scan', exact: true }).click();
};

test('Barcode Scanning - Dialog', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  // Attempt scan with invalid data
  await page.getByRole('button', { name: 'barcode-scan-button-any' }).click();
  await scan(page, 'invalid-barcode-123');
  await page.getByText('No match found for barcode').waitFor();

  // Attempt scan with "legacy" barcode format
  await scan(page, '{"part": 15}');

  await page.getByText('Part: R_550R_0805_1%', { exact: true }).waitFor();
  await page.getByText('Available:').waitFor();
  await page.getByText('Required:').waitFor();

  // Attempt scan with "modern" barcode format
  await page.getByRole('button', { name: 'barcode-scan-button-any' }).click();
  await scan(page, 'INV-BO0010');

  await page.getByText('Build Order: BO0010').waitFor();
  await page.getByText('Making a high level assembly part').waitFor();
});

test('Barcode Scanning - Basic', async ({ browser }) => {
  const page = await doCachedLogin(browser);

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

test('Barcode Scanning - Part', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'scan/' });

  await scan(page, '{"part": 1}');

  await page.getByText('R_10R_0402_1%').waitFor();
  await page.getByText('Stock:').waitFor();
  await page.getByRole('cell', { name: 'part', exact: true }).waitFor();
});

test('Barcode Scanning - Stockitem', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'scan/' });
  await scan(page, '{"stockitem": 408}');

  await page.getByText('1551ABK').waitFor();
  await page.getByText('Quantity: 100').waitFor();
  await page.getByRole('cell', { name: 'Quantity: 100' }).waitFor();
});

test('Barcode Scanning - StockLocation', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'scan/' });

  await scan(page, '{"stocklocation": 3}');

  // stocklocation: 3
  await page.getByText('Factory/Storage Room B', { exact: true }).waitFor();
  await page.getByText('Storage Room B (green door)').waitFor();
  await page
    .getByRole('cell', { name: 'stocklocation', exact: true })
    .waitFor();
});

test('Barcode Scanning - SupplierPart', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'scan/' });
  await scan(page, '{"supplierpart": 204}');

  await page.waitForLoadState('networkidle');
  await page.getByText('1551ABK').first().waitFor();
  await page.getByRole('cell', { name: 'supplierpart', exact: true }).waitFor();
});

test('Barcode Scanning - PurchaseOrder', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'scan/' });
  await scan(page, '{"purchaseorder": 12}');

  // purchaseorder: 12
  await page.getByText('PO0012').waitFor();
  await page.getByText('Wire from Wirey').waitFor();
  await page
    .getByRole('cell', { name: 'purchaseorder', exact: true })
    .waitFor();
});

test('Barcode Scanning - SalesOrder', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'scan/' });

  await scan(page, '{"salesorder": 6}');

  // salesorder: 6
  await page.getByText('SO0006').waitFor();
  await page.getByText('Selling more stuff to this').waitFor();
  await page.getByRole('cell', { name: 'salesorder', exact: true }).waitFor();
});

test('Barcode Scanning - Build', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'scan/' });
  await scan(page, '{"build": 8}');

  // build: 8
  await page.getByText('BO0008').waitFor();
  await page.getByText('PCBA build').waitFor();
  await page.getByRole('cell', { name: 'build', exact: true }).waitFor();
});

test('Barcode Scanning - Forms', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    username: 'admin',
    password: 'inventree',
    url: '/stock/location/index/stock-items'
  });

  // Ensure the user setting is enabled
  const api = await createApi({});

  let patched = false;

  await api
    .patch('/api/settings/user/BARCODE_IN_FORM_FIELDS/', {
      data: {
        value: true
      }
    })
    .then((response) => {
      patched = response.status() === 200;
    });

  // Assert that the setting was patched successfully
  if (!patched) {
    throw new Error('Could not patch user setting: BARCODE_IN_FORM_FIELDS');
  }

  await page.reload();

  // Open the "Add Stock Item" form
  await page
    .getByRole('button', { name: 'action-button-add-stock-item' })
    .click();

  // Fill out the "part" data
  await page.getByRole('button', { name: 'barcode-scan-button-part' }).click();
  await page
    .getByRole('textbox', { name: 'barcode-scan-keyboard-input' })
    .fill('INV-PA99');
  await page.getByRole('button', { name: 'Scan', exact: true }).click();
  await page.getByText('Red Round Table').waitFor();

  // Fill out the "location" data
  await page
    .getByRole('button', { name: 'barcode-scan-button-stocklocation' })
    .click();
  await page
    .getByRole('textbox', { name: 'barcode-scan-keyboard-input' })
    .fill('INV-SL37');
  await page.getByRole('button', { name: 'Scan', exact: true }).click();
  await page.getByText('Offsite Storage').waitFor();
});
