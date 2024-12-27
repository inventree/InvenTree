import { test } from '../baseFixtures.ts';
import { baseUrl } from '../defaults.ts';
import { clearTableFilters, setTableChoiceFilter } from '../helpers.ts';
import { doQuickLogin } from '../login.ts';

test('Sales Orders - Basic Tests', async ({ page }) => {
  await doQuickLogin(page);

  await page.goto(`${baseUrl}/home`);
  await page.getByRole('tab', { name: 'Sales' }).click();
  await page.getByRole('tab', { name: 'Sales Orders' }).click();

  // Check for expected text in the table
  await page.getByRole('tab', { name: 'Sales Orders' }).waitFor();

  await clearTableFilters(page);

  await setTableChoiceFilter(page, 'status', 'On Hold');

  await page.getByText('On Hold').first().waitFor();

  // Navigate to a particular sales order
  await page.getByRole('cell', { name: 'SO0003' }).click();

  // Order is "on hold". We will "issue" it and then place on hold again
  await page.getByText('Selling stuff').first().waitFor();
  await page.getByText('On Hold').first().waitFor();
  await page.getByRole('button', { name: 'Issue Order' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();

  // Order should now be "in progress"
  await page.getByText('In Progress').first().waitFor();
  await page.getByRole('button', { name: 'Ship Order' }).waitFor();

  await page.getByLabel('action-menu-order-actions').click();

  await page.getByLabel('action-menu-order-actions-edit').waitFor();
  await page.getByLabel('action-menu-order-actions-duplicate').waitFor();
  await page.getByLabel('action-menu-order-actions-cancel').waitFor();

  // Mark the order as "on hold" again
  await page.getByLabel('action-menu-order-actions-hold').click();
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.getByText('On Hold').first().waitFor();
  await page.getByRole('button', { name: 'Issue Order' }).waitFor();
});

test('Sales Orders - Shipments', async ({ page }) => {
  await doQuickLogin(page);

  await page.goto(`${baseUrl}/home`);
  await page.getByRole('tab', { name: 'Sales' }).click();
  await page.getByRole('tab', { name: 'Sales Orders' }).click();

  // Click through to a particular sales order
  await page.getByRole('tab', { name: 'Sales Orders' }).waitFor();
  await page.getByRole('cell', { name: 'SO0006' }).first().click();
  await page.getByRole('tab', { name: 'Shipments' }).click();

  // Create a new shipment
  await page.getByLabel('action-button-add-shipment').click();
  await page.getByLabel('text-field-tracking_number').fill('1234567890');
  await page.getByLabel('text-field-invoice_number').fill('9876543210');
  await page.getByRole('button', { name: 'Submit' }).click();

  // Expected field error
  await page
    .getByText('The fields order, reference must make a unique set')
    .first()
    .waitFor();
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Edit one of the existing shipments
  await page.getByLabel('row-action-menu-0').click();
  await page.getByRole('menuitem', { name: 'Edit' }).click();

  // Ensure the form has loaded
  await page.waitForTimeout(500);

  let tracking_number = await page
    .getByLabel('text-field-tracking_number')
    .inputValue();

  if (!tracking_number) {
    tracking_number = '1234567890';
  } else if (tracking_number.endsWith('x')) {
    // Remove the 'x' from the end of the tracking number
    tracking_number = tracking_number.substring(0, tracking_number.length - 1);
  } else {
    // Add an 'x' to the end of the tracking number
    tracking_number += 'x';
  }

  // Change the tracking number
  await page.getByLabel('text-field-tracking_number').fill(tracking_number);
  await page.waitForTimeout(250);
  await page.getByRole('button', { name: 'Submit' }).click();

  // Click through to a particular shipment
  await page.getByLabel('row-action-menu-0').click();
  await page.getByRole('menuitem', { name: 'View Shipment' }).click();

  // Click through the various tabs
  await page.getByRole('tab', { name: 'Attachments' }).click();
  await page.getByRole('tab', { name: 'Notes' }).click();
  await page.getByRole('tab', { name: 'Assigned Items' }).click();

  // Ensure assigned items table loads correctly
  await page.getByRole('cell', { name: 'BATCH-001' }).first().waitFor();

  await page.getByRole('tab', { name: 'Shipment Details' }).click();

  // The "new" tracking number should be visible
  await page.getByText(tracking_number).waitFor();

  // Link back to sales order
  await page.getByRole('link', { name: 'SO0006' }).click();

  // Let's try to allocate some stock
  await page.getByRole('tab', { name: 'Line Items' }).click();
  await page.getByLabel('row-action-menu-1').click();
  await page.getByRole('menuitem', { name: 'Allocate stock' }).click();
  await page
    .getByText('Select the source location for the stock allocation')
    .waitFor();
  await page.getByLabel('number-field-quantity').fill('123');
  await page.getByLabel('related-field-stock_item').click();
  await page.getByText('Quantity: 42').click();
  await page.getByRole('button', { name: 'Cancel' }).click();
});

test('Purchase Orders', async ({ page }) => {
  await doQuickLogin(page);

  await page.goto(`${baseUrl}/home`);
  await page.getByRole('tab', { name: 'Purchasing' }).click();
  await page.getByRole('tab', { name: 'Purchase Orders' }).click();

  // Check for expected values
  await page.getByRole('cell', { name: 'PO0014' }).waitFor();
  await page.getByText('Wire-E-Coyote').waitFor();
  await page.getByText('Cancelled').first().waitFor();
  await page.getByText('Pending').first().waitFor();
  await page.getByText('On Hold').first().waitFor();

  // Click through to a particular purchase order
  await page.getByRole('cell', { name: 'PO0013' }).click();

  await page.getByRole('button', { name: 'Issue Order' }).waitFor();
});

test('Purchase Orders - Barcodes', async ({ page }) => {
  await doQuickLogin(page);

  await page.goto(`${baseUrl}/purchasing/purchase-order/13/detail`);
  await page.getByRole('button', { name: 'Issue Order' }).waitFor();

  // Display QR code
  await page.getByLabel('action-menu-barcode-actions').click();
  await page.getByLabel('action-menu-barcode-actions-view').click();
  await page.getByRole('img', { name: 'QR Code' }).waitFor();
  await page.getByRole('banner').getByRole('button').click();

  // Link to barcode
  await page.getByLabel('action-menu-barcode-actions').click();
  await page.getByLabel('action-menu-barcode-actions-link-barcode').click();
  await page.getByRole('heading', { name: 'Link Barcode' }).waitFor();
  await page
    .getByPlaceholder('Scan barcode data here using')
    .fill('1234567890');
  await page.getByRole('button', { name: 'Link' }).click();
  await page.getByRole('button', { name: 'Issue Order' }).waitFor();

  // Unlink barcode
  await page.getByLabel('action-menu-barcode-actions').click();
  await page.getByLabel('action-menu-barcode-actions-unlink-barcode').click();
  await page.getByRole('heading', { name: 'Unlink Barcode' }).waitFor();
  await page.getByText('This will remove the link to').waitFor();
  await page.getByRole('button', { name: 'Unlink Barcode' }).click();
  await page.waitForTimeout(500);
  await page.getByRole('button', { name: 'Issue Order' }).waitFor();
});
