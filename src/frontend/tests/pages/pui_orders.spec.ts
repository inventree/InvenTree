import { test } from '../baseFixtures.ts';
import { baseUrl } from '../defaults.ts';
import { doQuickLogin } from '../login.ts';

test('PUI - Sales Orders', async ({ page }) => {
  await doQuickLogin(page);

  await page.goto(`${baseUrl}/home`);
  await page.getByRole('tab', { name: 'Sales' }).click();
  await page.getByRole('tab', { name: 'Sales Orders' }).click();

  // Check for expected text in the table
  await page.getByRole('tab', { name: 'Sales Orders' }).waitFor();
  await page.getByText('In Progress').first().waitFor();
  await page.getByText('On Hold').first().waitFor();

  // Navigate to a particular sales order
  await page.getByRole('cell', { name: 'SO0003' }).click();

  // Order is "on hold". We will "issue" it and then place on hold again
  await page.getByText('Sales Order: SO0003').waitFor();
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

test('PUI - Purchase Orders', async ({ page }) => {
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

test('PUI - Purchase Orders - Barcodes', async ({ page }) => {
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
