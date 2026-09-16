import type { Locator } from '@playwright/test';
import { expect, test } from './baseFixtures.js';
import { adminuser } from './defaults.js';
import { activateTableView, loadTab, navigate } from './helpers.js';
import { doCachedLogin } from './login.js';
import { setPluginState } from './settings.js';

// Test for the label editing interface
test('Printing - Label Editing', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    user: adminuser,
    url: 'settings/admin/labels'
  });

  // Open a particular label template for editing
  await page.getByRole('cell', { name: 'Sample build line label' }).click();

  // Await expected entries
  await page.getByRole('tab', { name: 'PDF Preview' }).waitFor();
  await page.getByText('This is an example template').waitFor();
  await page
    .locator('div')
    .filter({ hasText: /^BO\d+$/ })
    .first()
    .waitFor();
});

/*
 * Test for label printing.
 * Select a number of stock items from the table,
 * and print labels against them
 */
test('Printing - Label Printing', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'stock/location/index/' });

  await page.waitForURL('**/web/stock/location/**');

  await loadTab(page, 'Stock Items');

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
  await page.getByText('InvenTreeLabelMachine').last().click();

  // Select label template
  await page.getByLabel('related-field-template').click();
  await page
    .getByRole('option', { name: 'InvenTree Stock Item Label' })
    .click();

  await page.getByLabel('related-field-plugin').click();
  await page.getByRole('option', { name: 'InvenTreeLabel provides' }).click();

  // Submit the print form (second time should result in success)
  await page.getByRole('button', { name: 'Print', exact: true }).isEnabled();
  await page.getByRole('button', { name: 'Print', exact: true }).click();

  const successMessage = page
    .getByText('Process completed successfully')
    .first();
  await successMessage.waitFor();
  await successMessage.waitFor({ state: 'hidden' });

  // Re-open print dialog to verify persistence (issue #12129)
  await page
    .getByLabel('Stock Items')
    .getByLabel('action-menu-printing-actions')
    .click();
  await page.getByLabel('action-menu-printing-actions-print-labels').click();

  const labelDialog = page.getByRole('dialog', { name: 'Print Label' });

  // Wait for the dialog to fully load
  await labelDialog.getByLabel('related-field-template').waitFor();
  await labelDialog.getByLabel('related-field-plugin').waitFor();

  // Verify the last-used template is preselected
  await expect(labelDialog).toContainText('InvenTree Stock Item Label');

  // Verify the last-used plugin is preselected
  await expect(labelDialog).toContainText('InvenTreeLabel');

  // Submit again without re-selecting template or plugin
  const printResponse = page.waitForResponse(
    (response) =>
      response.url().includes('/api/label/print/') &&
      response.request().method() === 'POST' &&
      response.ok()
  );
  await labelDialog.getByRole('button', { name: 'Print', exact: true }).click();

  await printResponse;

  await page.context().close();
});

/*
 * Test for report printing
 * Navigate to a PurchaseOrder detail page,
 * and print a report against it.
 */
test('Printing - Report Printing', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'stock/location/index/' });

  await page.waitForURL('**/web/stock/location/**');

  // Navigate to a specific PurchaseOrder
  await page.getByRole('tab', { name: 'Purchasing' }).click();
  await loadTab(page, 'Purchase Orders');
  await activateTableView(page);

  await page.getByRole('cell', { name: 'PO0013' }).click();

  // Select "print report"
  await page.getByLabel('action-menu-printing-actions').click();
  await page.getByLabel('action-menu-printing-actions-print-reports').click();

  // Template should auto-fill (there is only one template available)
  await page.getByText('Sample purchase order report').waitFor();
  await page.getByRole('button', { name: 'Print', exact: true }).isEnabled();
  await page.getByRole('button', { name: 'Print', exact: true }).click();
  await page.getByText('Process completed successfully').first().waitFor();

  await page.context().close();
});

test('Printing - Report Editing', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    user: adminuser
  });

  // activate the sample plugin for this test
  await setPluginState({
    plugin: 'sampleui',
    state: true
  });

  // Navigate to the admin center
  await page.getByRole('button', { name: 'admin' }).click();
  await page.getByRole('menuitem', { name: 'Admin Center' }).click();
  await loadTab(page, 'Label Templates');
  await page
    .getByRole('cell', { name: 'InvenTree Stock Item Label (' })
    .click();

  // check that styles are applied correctly
  await expect(page.getByText('{% block style %}')).toBeVisible();
  const element: Locator = page.getByText('block').first();
  const color = await element.evaluate((el) => {
    return window.getComputedStyle(el).getPropertyValue('color');
  });
  expect(color).toBe('rgb(78, 201, 176)');

  // Generate preview
  await page.getByLabel('split-button-preview-options-action').click();
  await page
    .getByLabel('split-button-preview-options-item-preview-save', {
      exact: true
    })
    .click();

  await page.getByRole('button', { name: 'Save & Reload' }).click();

  await page.getByText('The preview has been updated').waitFor();

  // Test plugin provided editors
  await page.getByRole('tab', { name: 'Sample Template Editor' }).click();
  const textarea = page.locator('#sample-template-editor-textarea');
  const textareaValue = await textarea.inputValue();
  expect(textareaValue).toContain(
    `<img class='qr' alt="{% trans 'QR Code' %}" src='{% qrcode qr_data %}'>`
  );
  textarea.fill(`${textareaValue}\nHello world`);

  // Switch back and forth to see if the changed contents get correctly passed between the hooks
  await page.getByRole('tab', { name: 'Code', exact: true }).click();
  await page.getByRole('tab', { name: 'Sample Template Editor' }).click();
  const newTextareaValue = await page
    .locator('#sample-template-editor-textarea')
    .inputValue();
  expect(newTextareaValue).toMatch(/\nHello world$/);

  // Test plugin provided previews
  await page.getByRole('tab', { name: 'Sample Template Preview' }).click();
  await page.getByRole('heading', { name: 'Hello world' }).waitFor();
  const consoleLogPromise = page.waitForEvent('console');
  await page
    .getByLabel('split-button-preview-options', { exact: true })
    .click();
  const msg = (await consoleLogPromise).args();
  expect(await msg[0].jsonValue()).toBe('updatePreview');
  expect(await msg[1].jsonValue()).toBe(newTextareaValue);

  // deactivate the sample plugin again after the test
  await setPluginState({
    plugin: 'sampleui',
    state: false
  });
});

// Test report printing with an intentionally broken template, to verify that errors are handled gracefully
test('Printing - Broken Template', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    user: adminuser,
    url: 'sales/sales-order/14/detail'
  });

  // Print report from the "sales order" detail page
  await page
    .getByRole('button', { name: 'action-menu-printing-actions' })
    .click();
  await page
    .getByRole('menuitem', {
      name: 'action-menu-printing-actions-print-reports'
    })
    .click();
  await page
    .getByRole('combobox', { name: 'related-field-template' })
    .fill('broken');
  await page.getByText('Broken Sales Order Report').click();
  await page.getByRole('button', { name: 'Print', exact: true }).click();

  // Expected error message
  await page
    .getByText('parameter tag requires a valid Model instance')
    .waitFor();

  // Next, check error message from the template editor preview
  await navigate(page, 'settings/admin/reports');
  await page
    .getByRole('textbox', { name: 'table-search-input' })
    .fill('broken');
  await page.getByRole('cell', { name: 'Broken Sales Order Report' }).click();

  await page.getByLabel('split-button-preview-options-action').click();

  await page
    .getByLabel('split-button-preview-options-item-preview-save', {
      exact: true
    })
    .click();

  await page.getByRole('button', { name: 'Save & Reload' }).click();

  // Expected error messages
  await page.getByText('Error rendering template').waitFor();
  await page
    .getByText('parameter tag requires a valid Model instance')
    .waitFor();
});
