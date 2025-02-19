import test from '@playwright/test';
import { globalSearch, navigate } from './helpers';
import { doQuickLogin } from './login';

// Helper function to open the export data dialog
const openExportDialog = async (page) => {
  await page.getByLabel('table-export-data').click();
  await page.getByText('Export Format *', { exact: true }).waitFor();
  await page.getByText('Export Plugin *', { exact: true }).waitFor();
};

// Test data export for various order types
test('Exporting - Orders', async ({ page }) => {
  await doQuickLogin(page, 'steven', 'wizardstaff');

  // Download list of purchase orders
  await navigate(page, 'purchasing/index/purchase-orders');

  await openExportDialog(page);

  // // Select export format
  await page.getByLabel('choice-field-export_format').click();
  await page.getByRole('option', { name: 'Excel' }).click();

  // // Select export plugin (should only be one option here)
  await page.getByLabel('choice-field-export_plugin').click();
  await page.getByRole('option', { name: 'InvenTree Exporter' }).click();

  // // Export the data
  await page.getByRole('button', { name: 'Export', exact: true }).click();
  await page.getByText('Data exported successfully').waitFor();

  // Download list of purchase order items
  await page.getByRole('cell', { name: 'PO0011' }).click();
  await page.getByRole('tab', { name: 'Line Items' }).click();
  await openExportDialog(page);
  await page.getByRole('button', { name: 'Export', exact: true }).click();
  await page.getByText('Data exported successfully').waitFor();
});

// Test for custom BOM exporter
test('Exporting - BOM', async ({ page }) => {
  await doQuickLogin(page, 'steven', 'wizardstaff');

  await globalSearch(page, 'MAST');
  await page.getByLabel('search-group-results-part').locator('a').click();
  await page.getByRole('tab', { name: 'Bill of Materials' }).click();
  await openExportDialog(page);

  // Select export format
  await page.getByLabel('choice-field-export_format').click();
  await page.getByRole('option', { name: 'TSV' }).click();

  // Select BOM plugin
  await page.getByLabel('choice-field-export_plugin').click();
  await page.getByRole('option', { name: 'BOM Exporter' }).click();

  // Now, adjust the settings specific to the BOM exporter
  await page.getByLabel('number-field-export_levels').fill('3');
  await page
    .locator('label')
    .filter({ hasText: 'Pricing DataInclude part' })
    .locator('span')
    .nth(1)
    .click();
  await page
    .locator('label')
    .filter({ hasText: 'Parameter DataInclude part' })
    .locator('span')
    .nth(1)
    .click();

  await page.getByRole('button', { name: 'Export', exact: true }).click();
  await page.getByText('Data exported successfully').waitFor();
});
