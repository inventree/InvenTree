import { expect } from '@playwright/test';
import { test } from '../baseFixtures.ts';
import {
  clearTableFilters,
  clickOnRowMenu,
  globalSearch,
  loadTab,
  setTableChoiceFilter
} from '../helpers.ts';
import { doCachedLogin } from '../login.ts';

test('Sales Orders - Tabs', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'sales/index/' });

  await page.waitForURL('**/web/sales/**');

  // Sales Orders panel
  await loadTab(page, 'Sales Orders');
  await page.waitForURL('**/web/sales/index/salesorders');

  await page
    .getByRole('button', { name: 'segmented-icon-control-parametric' })
    .click();
  await page
    .getByRole('button', { name: 'segmented-icon-control-calendar' })
    .click();
  await page
    .getByRole('button', { name: 'segmented-icon-control-table' })
    .click();

  // Pending Shipments panel
  await loadTab(page, 'Pending Shipments');
  await page.getByRole('cell', { name: 'SO0007' }).waitFor();
  await page.getByRole('button', { name: 'Shipment Reference' }).waitFor();

  // Return Orders panel
  await loadTab(page, 'Return Orders');
  await page.getByRole('cell', { name: 'NOISE-COMPLAINT' }).waitFor();

  await page
    .getByRole('button', { name: 'segmented-icon-control-parametric' })
    .click();
  await page
    .getByRole('button', { name: 'segmented-icon-control-calendar' })
    .click();
  await page
    .getByRole('button', { name: 'segmented-icon-control-table' })
    .click();

  // Customers
  await loadTab(page, 'Customers');

  await page
    .getByRole('button', { name: 'segmented-icon-control-parametric' })
    .click();
  await page
    .getByRole('button', { name: 'segmented-icon-control-table' })
    .click();

  await page.getByText('Customer A').click();
  await loadTab(page, 'Notes');
  await loadTab(page, 'Attachments');
  await loadTab(page, 'Contacts');
  await loadTab(page, 'Assigned Stock');
  await loadTab(page, 'Return Orders');
  await loadTab(page, 'Sales Orders');
  await loadTab(page, 'Contacts');
  await page.getByRole('cell', { name: 'Dorathy Gross' }).waitFor();
  await page
    .getByRole('row', { name: 'Dorathy Gross 	dorathy.gross@customer.com' })
    .waitFor();

  // Sales Order Details
  await loadTab(page, 'Sales Orders');

  await clearTableFilters(page);

  await page.getByRole('cell', { name: 'SO0001' }).click();
  await page
    .getByLabel('Order Details')
    .getByText('Selling some stuff')
    .waitFor();
  await loadTab(page, 'Line Items');
  await loadTab(page, 'Shipments');
  await loadTab(page, 'Build Orders');
  await page.getByText('No records found').first().waitFor();
  await loadTab(page, 'Attachments');
  await page.getByText('No attachments found').first().waitFor();
  await loadTab(page, 'Notes');
  await loadTab(page, 'Order Details');

  // Return Order Details
  await page.getByRole('link', { name: 'Customer A' }).click();
  await loadTab(page, 'Return Orders');
  await page.getByRole('cell', { name: 'RMA-' }).click();
  await page.getByText('RMA-0001', { exact: true }).waitFor();
  await loadTab(page, 'Line Items');
  await loadTab(page, 'Attachments');
  await loadTab(page, 'Notes');
});

test('Sales Orders - Basic Tests', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  await page.getByRole('tab', { name: 'Sales' }).click();
  await page.waitForURL('**/sales/index/**');

  await loadTab(page, 'Sales Orders');

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

test('Sales Orders - Shipments', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  await page.getByRole('tab', { name: 'Sales' }).click();
  await page.waitForURL('**/sales/index/**');

  await loadTab(page, 'Sales Orders');

  await clearTableFilters(page);

  // Click through to a particular sales order
  await page.getByRole('cell', { name: 'SO0006' }).first().click();
  await loadTab(page, 'Shipments');
  await clearTableFilters(page);

  // Create a new shipment
  await page.getByLabel('action-button-add-shipment').click();
  await page
    .getByLabel('text-field-tracking_number', { exact: true })
    .fill('1234567890');
  await page
    .getByLabel('text-field-invoice_number', { exact: true })
    .fill('9876543210');
  await page.getByRole('button', { name: 'Submit' }).click();

  // Expected field error
  await page
    .getByText('The fields order, reference must make a unique set')
    .first()
    .waitFor();
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Edit one of the existing shipments
  const cell = page.getByRole('cell', { name: /SHIP-XYZ/ });
  await clickOnRowMenu(cell);
  await page.getByRole('menuitem', { name: 'Edit' }).click();

  // Ensure the form has loaded
  await page.waitForLoadState('networkidle');

  let tracking_number = await page
    .getByLabel('text-field-tracking_number', { exact: true })
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
  await page
    .getByLabel('text-field-tracking_number', { exact: true })
    .fill(tracking_number);
  await page.waitForTimeout(250);
  await page.getByRole('button', { name: 'Submit' }).click();

  // Click through to a particular shipment
  await page.getByRole('cell', { name: tracking_number }).click();

  // Click through the various tabs
  await loadTab(page, 'Attachments');
  await loadTab(page, 'Notes');
  await loadTab(page, 'Allocated Stock');

  // Ensure assigned items table loads correctly
  await page.getByRole('cell', { name: 'BATCH-001' }).first().waitFor();

  await loadTab(page, 'Shipment Details');

  // The "new" tracking number should be visible
  await page.getByText(tracking_number).waitFor();

  // Link back to sales order
  await page.getByRole('link', { name: 'breadcrumb-1-so0006' }).click();

  // Let's try to allocate some stock
  await loadTab(page, 'Line Items');

  await clickOnRowMenu(page.getByRole('cell', { name: 'WID-REV-A' }));
  await page.getByRole('menuitem', { name: 'Allocate stock' }).click();
  await page
    .getByText('Select the source location for the stock allocation')
    .waitFor();
  await page.getByLabel('number-field-quantity').fill('123');
  await page.getByLabel('related-field-stock_item').fill('42');

  await page.getByText('Serial Number: 42').click();
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Search for shipment by tracking number
  await globalSearch(page, 'TRK-002');

  await page
    .getByText(/SO0009/)
    .first()
    .click();

  // Search for shipment by invoice number
  await globalSearch(page, 'INV-123');

  await page
    .getByText(/SO0025/)
    .first()
    .click();
});

test('Sales Orders - Duplicate', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'sales/sales-order/14/detail'
  });

  await page.getByLabel('action-menu-order-actions').click();
  await page.getByLabel('action-menu-order-actions-duplicate').click();

  // Ensure a new reference is suggested
  await expect(
    page.getByLabel('text-field-reference', { exact: true })
  ).not.toBeEmpty();

  // Submit the duplicate request and ensure it completes
  await page.getByRole('button', { name: 'Submit' }).isEnabled();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByRole('tab', { name: 'Order Details' }).waitFor();
  await page.getByRole('tab', { name: 'Order Details' }).click();

  await page.getByText('Pending').first().waitFor();

  // Issue the order
  await page.getByRole('button', { name: 'Issue Order' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('In Progress').first().waitFor();

  // Cancel the outstanding shipment
  await loadTab(page, 'Shipments');
  await clearTableFilters(page);
  const cell = await page.getByRole('cell', { name: '1', exact: true });
  await clickOnRowMenu(cell);
  await page.getByRole('menuitem', { name: 'Cancel' }).click();
  await page.getByRole('button', { name: 'Delete' }).click();

  // Check for expected line items
  await loadTab(page, 'Line Items');
  await page.getByRole('cell', { name: 'SW-001' }).waitFor();
  await page.getByRole('cell', { name: 'SW-002' }).waitFor();
  await page.getByText('1 - 2 / 2').waitFor();

  // Ship the order
  await page.getByRole('button', { name: 'Ship Order' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();

  // Complete the order
  await page.getByRole('button', { name: 'Complete Order' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();

  // Go to the "details" tab
  await loadTab(page, 'Order Details');

  // Check for expected results
  // 2 line items completed, as they are both virtual (no stock)
  await page.getByText('Complete').first().waitFor();
  await page.getByText('2 / 2').waitFor();
});

/**
 * Test auto-calculation of price breaks on sales order line items
 */
test('Sales Orders - Price Breaks', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'sales/sales-order/14/line-items'
  });

  await page
    .getByRole('button', { name: 'action-button-add-line-item' })
    .click();
  await page.getByLabel('related-field-part').fill('software');
  await page.getByRole('option', { name: 'Software License' }).click();

  const priceBreaks = {
    1: 123,
    2: 123,
    10: 104,
    49: 104,
    56: 96,
    104: 78
  };

  for (const [qty, expectedPrice] of Object.entries(priceBreaks)) {
    await page.getByLabel('number-field-quantity').fill(qty);

    await expect(
      page.getByRole('textbox', { name: 'number-field-sale_price' })
    ).toHaveAttribute('placeholder', expectedPrice.toString(), {
      timeout: 500
    });
  }

  // Auto-fill the suggested sale price
  await page.getByLabel('field-sale_price-accept-placeholder').click();

  // The sale price field should now contain the suggested value
  await expect(
    page.getByRole('textbox', { name: 'number-field-sale_price' })
  ).toHaveValue('78', { timeout: 500 });
});
