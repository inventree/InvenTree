import { expect, test } from './baseFixtures.js';
import { baseUrl } from './defaults.js';
import { doQuickLogin } from './login.js';
import { setPluginState } from './settings.js';

/*
 * Test for label printing.
 * Select a number of stock items from the table,
 * and print labels against them
 */
test('Label Printing', async ({ page }) => {
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

  // Submit the print form (second time should result in success)
  await page.getByRole('button', { name: 'Print', exact: true }).isEnabled();
  await page.getByRole('button', { name: 'Print', exact: true }).click();

  await page.locator('#form-success').waitFor();
  await page.getByText('Label printing completed').waitFor();

  await page.context().close();
});

/*
 * Test for report printing
 * Navigate to a PurchaseOrder detail page,
 * and print a report against it.
 */
test('Report Printing', async ({ page }) => {
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

  // Submit the print form (should result in success)
  await page.getByRole('button', { name: 'Generate', exact: true }).isEnabled();
  await page.getByRole('button', { name: 'Generate', exact: true }).click();

  await page.locator('#form-success').waitFor();
  await page.getByText('Report printing completed').waitFor();

  await page.context().close();
});

test('Report Editing', async ({ page, request }) => {
  const [username, password] = ['admin', 'inventree'];
  await doQuickLogin(page, username, password);

  // activate the sample plugin for this test
  await setPluginState({
    request,
    plugin: 'sampleui',
    state: true
  });

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
  expect((await msg[1].jsonValue())[0]).toBe(newTextareaValue);

  // deactivate the sample plugin again after the test
  await setPluginState({
    request,
    plugin: 'sampleui',
    state: false
  });
});
