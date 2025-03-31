import test from '@playwright/test';
import { globalSearch, loadTab, navigate } from './helpers';
import { doCachedLogin } from './login';

// Helper function to open the export data dialog
const openExportDialog = async (page) => {
  await page.waitForLoadState('networkidle');
  await page.getByLabel('table-export-data').click();
  await page.getByText('Export Format *', { exact: true }).waitFor();
  await page.getByText('Export Plugin *', { exact: true }).waitFor();
};

// Test data export for various order types
test('Exporting - Orders', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    username: 'steven',
    password: 'wizardstaff',
    url: 'purchasing/index/purchase-orders'
  });

  await openExportDialog(page);

  // // Select export format
  await page.getByLabel('choice-field-export_format').click();
  await page.getByRole('option', { name: 'Excel' }).click();

  // // Select export plugin (should only be one option here)
  await page.getByLabel('choice-field-export_plugin').click();
  await page.getByRole('option', { name: 'InvenTree Exporter' }).click();

  // // Export the data
  await page.getByRole('button', { name: 'Export', exact: true }).click();
  await page.getByText('Process completed successfully').waitFor();

  // Download list of purchase order items
  await page.getByRole('cell', { name: 'PO0011' }).click();
  await loadTab(page, 'Line Items');
  await openExportDialog(page);
  await page.getByRole('button', { name: 'Export', exact: true }).click();
  await page.getByText('Process completed successfully').waitFor();

  // Download a list of build orders
  await navigate(page, 'manufacturing/index/buildorders/');
  await openExportDialog(page);
  await page.getByRole('button', { name: 'Export', exact: true }).click();
  await page.getByText('Process completed successfully').waitFor();

  // Finally, navigate to the admin center and ensure the export data is available
  await navigate(page, 'settings/admin/export/');

  // Check for expected outputs
  await page
    .getByRole('link', { name: /InvenTree_Build_.*\.csv/ })
    .first()
    .waitFor();
  await page
    .getByRole('link', { name: /InvenTree_PurchaseOrder_.*\.xlsx/ })
    .first()
    .waitFor();
  await page
    .getByRole('link', { name: /InvenTree_PurchaseOrderLineItem_.*\.csv/ })
    .first()
    .waitFor();

  // Delete all exported file outputs
  await page.getByRole('cell', { name: 'Select all records' }).click();
  await page.getByLabel('action-button-delete-selected').click();
  await page.getByRole('button', { name: 'Delete', exact: true }).click();
  await page.getByText('Items Deleted').waitFor();
});

// Test for custom BOM exporter
test('Exporting - BOM', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    username: 'steven',
    password: 'wizardstaff'
  });

  await globalSearch(page, 'MAST');
  await page.getByLabel('search-group-results-part').locator('a').click();
  await page.waitForLoadState('networkidle');
  await loadTab(page, 'Bill of Materials');
  await openExportDialog(page);

  // Select export format
  await page.getByLabel('choice-field-export_format').click();
  await page.getByRole('option', { name: 'TSV' }).click();
  await page.waitForLoadState('networkidle');

  // Select BOM plugin
  await page.getByLabel('choice-field-export_plugin').click();
  await page.getByRole('option', { name: 'BOM Exporter' }).click();
  await page.waitForLoadState('networkidle');

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
  await page.getByText('Process completed successfully').waitFor();

  // Finally, navigate to the admin center and ensure the export data is available
  await navigate(page, 'settings/admin/export/');

  await page.getByRole('cell', { name: 'bom-exporter' }).first().waitFor();
  await page
    .getByRole('link', { name: /InvenTree_BomItem_.*\.tsv/ })
    .first()
    .waitFor();

  // Required because we downloaded a file
  await page.context().close();
});
