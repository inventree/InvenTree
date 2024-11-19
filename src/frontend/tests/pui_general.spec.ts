import { test } from './baseFixtures.js';
import { baseUrl } from './defaults.js';
import { doQuickLogin } from './login.js';

test('Sales', async ({ page }) => {
  await doQuickLogin(page);

  await page.goto(`${baseUrl}/sales/index/`);
  await page.waitForURL('**/platform/sales/**');

  await page.getByRole('tab', { name: 'Sales Orders' }).click();
  await page.waitForURL('**/platform/sales/index/salesorders');
  await page.getByRole('tab', { name: 'Return Orders' }).click();

  // Customers
  await page.getByRole('tab', { name: 'Customers' }).click();
  await page.getByText('Customer A').click();
  await page.getByRole('tab', { name: 'Notes' }).click();
  await page.getByRole('tab', { name: 'Attachments' }).click();
  await page.getByRole('tab', { name: 'Contacts' }).click();
  await page.getByRole('tab', { name: 'Assigned Stock' }).click();
  await page.getByRole('tab', { name: 'Return Orders' }).click();
  await page.getByRole('tab', { name: 'Sales Orders' }).click();
  await page.getByRole('tab', { name: 'Contacts' }).click();
  await page.getByRole('cell', { name: 'Dorathy Gross' }).waitFor();
  await page
    .getByRole('row', { name: 'Dorathy Gross 	dorathy.gross@customer.com' })
    .waitFor();

  // Sales Order Details
  await page.getByRole('tab', { name: 'Sales Orders' }).click();
  await page.getByRole('cell', { name: 'SO0001' }).click();
  await page
    .getByLabel('Order Details')
    .getByText('Selling some stuff')
    .waitFor();
  await page.getByRole('tab', { name: 'Line Items' }).click();
  await page.getByRole('tab', { name: 'Shipments' }).click();
  await page.getByRole('tab', { name: 'Build Orders' }).click();
  await page.getByText('No records found').first().waitFor();
  await page.getByRole('tab', { name: 'Attachments' }).click();
  await page.getByText('No attachments found').first().waitFor();
  await page.getByRole('tab', { name: 'Notes' }).click();
  await page.getByRole('tab', { name: 'Order Details' }).click();

  // Return Order Details
  await page.getByRole('link', { name: 'Customer A' }).click();
  await page.getByRole('tab', { name: 'Return Orders' }).click();
  await page.getByRole('cell', { name: 'RMA-' }).click();
  await page.getByText('RMA-0001', { exact: true }).waitFor();
  await page.getByRole('tab', { name: 'Line Items' }).click();
  await page.getByRole('tab', { name: 'Attachments' }).click();
  await page.getByRole('tab', { name: 'Notes' }).click();
});

test('Company', async ({ page }) => {
  await doQuickLogin(page);

  await page.goto(`${baseUrl}/company/1/details`);
  await page.getByLabel('Details').getByText('DigiKey Electronics').waitFor();
  await page.getByRole('cell', { name: 'https://www.digikey.com/' }).waitFor();
  await page.getByRole('tab', { name: 'Supplied Parts' }).click();
  await page
    .getByRole('cell', { name: 'RR05P100KDTR-ND', exact: true })
    .waitFor();
  await page.getByRole('tab', { name: 'Purchase Orders' }).click();
  await page.getByRole('cell', { name: 'Molex connectors' }).first().waitFor();
  await page.getByRole('tab', { name: 'Stock Items' }).click();
  await page
    .getByRole('cell', { name: 'Blue plastic enclosure' })
    .first()
    .waitFor();
  await page.getByRole('tab', { name: 'Contacts' }).click();
  await page.getByRole('cell', { name: 'jimmy.mcleod@digikey.com' }).waitFor();
  await page.getByRole('tab', { name: 'Addresses' }).click();
  await page.getByRole('cell', { name: 'Carla Tunnel' }).waitFor();
  await page.getByRole('tab', { name: 'Attachments' }).click();
  await page.getByRole('tab', { name: 'Notes' }).click();

  // Let's edit the company details
  await page.getByLabel('action-menu-company-actions').click();
  await page.getByLabel('action-menu-company-actions-edit').click();

  await page.getByLabel('text-field-name').fill('');
  await page.getByLabel('text-field-website').fill('invalid-website');
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.getByText('This field may not be blank.').waitFor();
  await page.getByText('Enter a valid URL.').waitFor();
  await page.getByRole('button', { name: 'Cancel' }).click();
});

/**
 * Test for integration of django admin button
 */
test('Admin Button', async ({ page }) => {
  await doQuickLogin(page, 'admin', 'inventree');
  await page.goto(`${baseUrl}/company/1/details`);

  // Click on the admin button
  await page.getByLabel(/action-button-open-in-admin/).click();

  await page.waitForURL('**/test-admin/company/company/1/change/**');
  await page.getByRole('heading', { name: 'Change Company' }).waitFor();
  await page.getByRole('link', { name: 'View on site' }).waitFor();
});
