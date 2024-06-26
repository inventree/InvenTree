import { test } from './baseFixtures.js';
import { baseUrl } from './defaults.js';
import { doQuickLogin } from './login.js';

/*
 * Test for label printing.
 * Select a number of stock items from the table,
 * and print labels against them
 */
test('PUI - Label Printing', async ({ page }) => {
  await doQuickLogin(page);

  await page.goto(`${baseUrl}/stock/location/index/`);
  await page.waitForURL('**/platform/stock/location/**');

  await page.getByRole('tab', { name: 'Stock Items' }).click();

  // Select some labels
  await page.getByLabel('Select record 1', { exact: true }).click();
  await page.getByLabel('Select record 2', { exact: true }).click();
  await page.getByLabel('Select record 3', { exact: true }).click();

  await page
    .getByLabel('Stock Items')
    .getByLabel('action-menu-printing-actions')
    .click();
  await page.getByLabel('action-menu-printing-actions-print-labels').click();

  // Select plugin
  await page.getByLabel('related-field-plugin').click();
  await page.getByText('InvenTreeLabelSheet').click();

  // Select label template
  await page.getByLabel('related-field-template').click();
  await page.getByText('InvenTree Stock Item Label (').click();

  await page.waitForTimeout(100);

  // Submit the form (second time should result in success)
  await page.getByRole('button', { name: 'Submit' }).isEnabled();
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.locator('#form-success').waitFor();
  await page.getByText('Label printing completed').waitFor();

  await page.context().close();
});

/*
 * Test for report printing
 * Navigate to a PurchaseOrder detail page,
 * and print a report against it.
 */
test('PUI - Report Printing', async ({ page }) => {
  await doQuickLogin(page);

  await page.goto(`${baseUrl}/stock/location/index/`);
  await page.waitForURL('**/platform/stock/location/**');

  // Navigate to a specific PurchaseOrder
  await page.getByRole('tab', { name: 'Purchasing' }).click();
  await page.getByRole('cell', { name: 'PO0009' }).click();

  // Select "print report"
  await page.getByLabel('action-menu-printing-actions').click();
  await page.getByLabel('action-menu-printing-actions-print-reports').click();

  // Select template
  await page.getByLabel('related-field-template').click();
  await page.getByText('InvenTree Purchase Order').click();

  await page.waitForTimeout(100);

  // Submit the form (should result in success)
  await page.getByRole('button', { name: 'Submit' }).isEnabled();
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.locator('#form-success').waitFor();
  await page.getByText('Report printing completed').waitFor();

  await page.context().close();
});

test('PUI - Report Editing', async ({ page }) => {
  await doQuickLogin(page, 'admin', 'inventree');

  // Navigate to the admin center
  await page.getByRole('button', { name: 'admin' }).click();
  await page.getByRole('menuitem', { name: 'Admin Center' }).click();
  await page.getByRole('tab', { name: 'Label Templates' }).click();
  await page
    .getByRole('cell', { name: 'InvenTree Stock Item Label (' })
    .click();

  // Generate preview
  await page.getByLabel('split-button-preview-options-action').click();
  await page
    .getByLabel('split-button-preview-options-item-preview-save', {
      exact: true
    })
    .click();

  await page.getByRole('button', { name: 'Save & Reload' }).click();

  await page.getByText('The preview has been updated').waitFor();

  await page.context().close();
});
