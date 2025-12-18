import { expect } from '@playwright/test';
import { test } from '../baseFixtures.ts';
import {
  activateCalendarView,
  activateTableView,
  clearTableFilters,
  clickButtonIfVisible,
  clickOnRowMenu,
  loadTab,
  navigate,
  openFilterDrawer,
  setTableChoiceFilter
} from '../helpers.ts';
import { doCachedLogin } from '../login.ts';

test('Purchasing - Index', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'purchasing/index/' });

  // Purchase Orders tab
  await loadTab(page, 'Purchase Orders');
  await page
    .getByRole('button', { name: 'segmented-icon-control-parametric' })
    .click();

  await page
    .getByRole('button', { name: 'segmented-icon-control-calendar' })
    .click();
  await page.getByRole('button', { name: 'calendar-select-month' }).waitFor();
  await page
    .getByRole('button', { name: 'segmented-icon-control-table' })
    .click();

  // Suppliers tab
  await loadTab(page, 'Suppliers');
  await page
    .getByRole('button', { name: 'segmented-icon-control-parametric' })
    .click();
  await page
    .getByRole('button', { name: 'segmented-icon-control-table' })
    .click();

  // Supplier parts tab
  await loadTab(page, 'Supplier Parts');
  await page
    .getByRole('button', { name: 'segmented-icon-control-parametric' })
    .click();
  await page
    .getByRole('button', { name: 'segmented-icon-control-table' })
    .click();

  // Manufacturers tab
  await loadTab(page, 'Manufacturers');
  await page
    .getByRole('button', { name: 'segmented-icon-control-parametric' })
    .click();
  await page
    .getByRole('button', { name: 'segmented-icon-control-table' })
    .click();

  // Manufacturer parts tab
  await loadTab(page, 'Manufacturer Parts');
  await page
    .getByRole('button', { name: 'segmented-icon-control-parametric' })
    .click();
  await page
    .getByRole('button', { name: 'segmented-icon-control-table' })
    .click();
});

test('Purchase Orders - General', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  await page.getByRole('tab', { name: 'Purchasing' }).click();
  await page.waitForURL('**/purchasing/index/**');

  await page.getByRole('cell', { name: 'PO0012' }).click();
  await page.waitForTimeout(200);

  await loadTab(page, 'Line Items');
  await loadTab(page, 'Received Stock');
  await loadTab(page, 'Parameters');
  await loadTab(page, 'Attachments');

  await page.getByRole('tab', { name: 'Purchasing' }).click();
  await loadTab(page, 'Suppliers');
  await page.getByText('Arrow', { exact: true }).click();
  await page.waitForTimeout(200);

  await loadTab(page, 'Supplied Parts');
  await loadTab(page, 'Purchase Orders');
  await loadTab(page, 'Stock Items');
  await loadTab(page, 'Contacts');
  await loadTab(page, 'Addresses');
  await loadTab(page, 'Attachments');

  await page.getByRole('tab', { name: 'Purchasing' }).click();
  await loadTab(page, 'Manufacturers');
  await page.getByText('AVX Corporation').click();
  await page.waitForTimeout(200);

  await loadTab(page, 'Addresses');
  await page.getByRole('cell', { name: 'West Branch' }).click();
  await page.locator('.mantine-ScrollArea-root').click();
  await page
    .getByRole('row', { name: 'West Branch Yes Surf Avenue 9' })
    .getByRole('button')
    .click();
  await page.getByRole('menuitem', { name: 'Edit' }).click();

  await page.getByLabel('text-field-title', { exact: true }).waitFor();
  await page.getByLabel('text-field-line2', { exact: true }).waitFor();

  // Read the current value of the cell, to ensure we always *change* it!
  const value = await page
    .getByLabel('text-field-line2', { exact: true })
    .inputValue();
  await page
    .getByLabel('text-field-line2', { exact: true })
    .fill(value == 'old' ? 'new' : 'old');

  await page.getByRole('button', { name: 'Submit' }).isEnabled();

  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByRole('tab', { name: 'Details' }).waitFor();
});

test('Purchase Orders - Table', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  await page.getByRole('tab', { name: 'Purchasing' }).click();
  await page.waitForURL('**/purchasing/index/**');

  await loadTab(page, 'Purchase Orders');
  await activateTableView(page);

  await clearTableFilters(page);

  // Check for expected values
  await page.getByRole('cell', { name: 'PO0014' }).waitFor();
  await page.getByText('Wire-E-Coyote').waitFor();
  await page.getByText('Cancelled').first().waitFor();
  await page.getByText('Pending').first().waitFor();
  await page.getByText('On Hold').first().waitFor();

  // Filter by 'has start date'
  await setTableChoiceFilter(page, 'Has Start Date', 'Yes');
  await page.getByRole('cell', { name: 'Scheduled purchase order' }).waitFor();

  // Click through to a particular purchase order
  await page.getByRole('cell', { name: 'PO0015' }).click();
  await page.getByRole('button', { name: 'Issue Order' }).waitFor();

  // Expected values
  await page.getByText('2025-06-12').waitFor(); // Start Date
  await page.getByText('2025-07-17').waitFor(); // Target Date
});

test('Purchase Orders - Calendar', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  await page.getByRole('tab', { name: 'Purchasing' }).click();
  await page.waitForURL('**/purchasing/index/**');
  await loadTab(page, 'Purchase Orders');

  // Ensure view is in "calendar" mode
  await activateCalendarView(page);

  // Check for expected components
  await page.getByLabel('action-button-previous-month').waitFor();
  await page.getByLabel('action-button-next-month').waitFor();

  await page.getByLabel('calendar-select-month').click();
  await page.getByRole('button', { name: 'Jan' }).waitFor();
  await page.getByRole('button', { name: 'Feb' }).waitFor();
  await page.getByRole('button', { name: 'Dec' }).click();

  await page.getByText('December').waitFor();

  // Put back into table view
  await activateTableView(page);
});

test('Purchase Orders - Barcodes', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'purchasing/purchase-order/13/detail'
  });

  await page.getByRole('button', { name: 'Issue Order' }).waitFor();

  // Display QR code
  await page.getByLabel('action-menu-barcode-actions').click();
  await page.getByLabel('action-menu-barcode-actions-view').click();
  await page.getByRole('img', { name: 'QR Code' }).waitFor();
  await page.getByRole('banner').getByRole('button').click();

  // Un-link barcode if a link exists
  await page.getByLabel('action-menu-barcode-actions').click();
  await page.waitForTimeout(100);

  if (
    await page
      .getByLabel('action-menu-barcode-actions-unlink-barcode')
      .isVisible()
  ) {
    await page.getByLabel('action-menu-barcode-actions-unlink-barcode').click();
    await page.getByRole('button', { name: 'Unlink Barcode' }).click();
    await page.waitForTimeout(100);
  } else {
    await page.keyboard.press('Escape');
  }

  // Link to barcode
  await page.getByLabel('action-menu-barcode-actions', { exact: true }).click();
  await page.getByLabel('action-menu-barcode-actions-link-barcode').click();

  await page.getByLabel('barcode-input-scanner').click();

  // Simulate barcode scan
  await page.getByPlaceholder('Enter barcode data').fill('1234567890');
  await page.getByRole('button', { name: 'Scan', exact: true }).click();
  await page.waitForTimeout(250);

  await page.getByRole('button', { name: 'Issue Order' }).waitFor();

  // Ensure we can scan back to this page, with the associated barcode
  await page.getByRole('tab', { name: 'Sales' }).click();
  await page.waitForTimeout(250);

  await page.getByRole('button', { name: 'barcode-scan-button-any' }).click();

  await page.getByPlaceholder('Enter barcode data').fill('1234567890');
  await page.getByRole('button', { name: 'Scan', exact: true }).click();

  await page.getByText('Purchase Order: PO0013', { exact: true }).waitFor();

  // Unlink barcode
  await page.getByLabel('action-menu-barcode-actions').click();
  await page.getByLabel('action-menu-barcode-actions-unlink-barcode').click();
  await page.getByRole('heading', { name: 'Unlink Barcode' }).waitFor();
  await page.getByText('This will remove the link to').waitFor();
  await page.getByRole('button', { name: 'Unlink Barcode' }).click();
  await page.waitForTimeout(250);
  await page.getByRole('button', { name: 'Issue Order' }).waitFor();
});

test('Purchase Orders - Filters', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    username: 'reader',
    password: 'readonly'
  });

  await page.getByRole('tab', { name: 'Purchasing' }).click();
  await page.waitForURL('**/purchasing/index/**');

  await loadTab(page, 'Purchase Orders');
  await activateTableView(page);

  // Open filters drawer
  await openFilterDrawer(page);
  await clickButtonIfVisible(page, 'Clear Filters');

  await page.getByRole('button', { name: 'Add Filter' }).click();

  // Check for expected filter options
  await page.getByPlaceholder('Select filter').fill('before');
  await page.getByRole('option', { name: 'Created Before' }).waitFor();
  await page.getByRole('option', { name: 'Completed Before' }).waitFor();
  await page.getByRole('option', { name: 'Target Date Before' }).waitFor();

  await page.getByPlaceholder('Select filter').fill('after');
  await page.getByRole('option', { name: 'Created After' }).waitFor();
  await page.getByRole('option', { name: 'Completed After' }).waitFor();
  await page.getByRole('option', { name: 'Target Date After' }).waitFor();
});

test('Purchase Orders - Price Breaks', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'purchasing/purchase-order/14/line-items'
  });

  await page
    .getByRole('button', { name: 'action-button-add-line-item' })
    .click();
  await page.getByLabel('related-field-part').fill('002.01');
  await page.getByRole('option', { name: 'PCBWOY PCB-002.01' }).click();

  // Expected price-break values
  const priceBreaks = {
    1: 500,
    8: 500,
    10: 565,
    99: 565,
    999: 205
  };

  for (const [qty, expectedPrice] of Object.entries(priceBreaks)) {
    await page.getByLabel('number-field-quantity').fill(qty);

    await expect(
      page.getByRole('textbox', { name: 'number-field-purchase_price' })
    ).toHaveAttribute('placeholder', expectedPrice.toString(), {
      timeout: 500
    });
  }

  // Auto-fill the suggested sale price
  await page.getByLabel('field-purchase_price-accept-placeholder').click();

  await expect(
    page.getByRole('textbox', { name: 'number-field-purchase_price' })
  ).toHaveValue('205', { timeout: 500 });
});

test('Purchase Orders - Order Parts', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  // Open "Order Parts" wizard from the "parts" table
  await page.getByRole('tab', { name: 'Parts' }).click();
  await page.waitForURL('**/part/category/index/**');

  await page
    .getByLabel('panel-tabs-partcategory')
    .getByRole('tab', { name: 'Parts' })
    .click();

  // Select multiple parts
  for (let ii = 1; ii < 5; ii++) {
    await page.getByLabel(`Select record ${ii}`, { exact: true }).click();
  }

  await page.getByLabel('action-menu-part-actions').click();
  await page.getByLabel('action-menu-part-actions-order-parts').click();
  await page
    .getByRole('heading', { name: 'Order Parts' })
    .locator('div')
    .first()
    .waitFor();
  await page.getByRole('banner').getByRole('button').click();

  // Open "Order Parts" wizard from the "Stock Items" table
  await page.getByRole('tab', { name: 'Stock' }).click();
  await loadTab(page, 'Stock Items');

  // Select multiple stock items
  for (let ii = 2; ii < 7; ii += 2) {
    await page.getByLabel(`Select record ${ii}`, { exact: true }).click();
  }

  await page.getByRole('button', { name: 'action-button-order-items' }).click();
  await page.getByRole('banner').getByRole('button').click();

  // Order from the part detail page
  await navigate(page, 'part/69/');
  await page.waitForURL('**/part/69/**');

  await page.getByLabel('action-menu-stock-actions').click();
  await page.getByLabel('action-menu-stock-actions-order').click();

  // Select supplier part
  await page.getByLabel('related-field-supplier_part').click();
  await page
    .getByRole('option', { name: 'Thumbnail DigiKey WM1731-ND' })
    .click();

  // Option to create a new supplier part
  await page.getByLabel('action-button-new-supplier-part').click();
  await page.getByLabel('related-field-supplier', { exact: true }).click();
  await page.getByText('Future').click();
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Select purchase order
  await page.getByLabel('related-field-purchase_order').click();
  await page.getByText('PO0001').click();

  // Option to create a new purchase order
  await page.getByLabel('action-button-new-purchase-order').click();
  await page.getByLabel('related-field-project_code').click();
  await page.getByText('PRJ-PHO').click();
  await page.getByRole('button', { name: 'Cancel' }).click();

  await page.getByLabel('number-field-quantity').fill('100');

  // Add the part to the purchase order
  await page.getByLabel('action-button-add-to-selected').click();
  await page.getByLabel('number-field-quantity').fill('100');
  await page.waitForTimeout(250);
  await page.getByRole('button', { name: 'Submit' }).click();
  await page
    .getByText('All selected parts added to a purchase order')
    .waitFor();
});

/**
 * Tests for receiving items against a purchase order
 */
test('Purchase Orders - Receive Items', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  await page.getByRole('tab', { name: 'Purchasing' }).click();
  await page.waitForURL('**/purchasing/index/**');

  await page.getByRole('cell', { name: 'PO0014' }).click();

  await loadTab(page, 'Order Details');

  // Select all line items to receive
  await loadTab(page, 'Line Items');

  await page.getByLabel('Select all records').click();
  await page.waitForTimeout(200);
  await page.getByLabel('action-button-receive-items').click();

  // Check for display of individual locations
  await page
    .getByRole('cell', { name: /Choose Location/ })
    .getByText('Parts Bins')
    .waitFor();
  await page
    .getByRole('cell', { name: /Choose Location/ })
    .getByText('Room 101')
    .waitFor();

  await page.getByText('Mechanical Lab').first().waitFor();

  await page.getByRole('button', { name: 'Cancel' }).click();

  // Let's actually receive an item (with custom values)
  await navigate(page, 'purchasing/purchase-order/2/line-items');

  const cell = await page.getByText('Red Paint', { exact: true });
  await clickOnRowMenu(cell);
  await page.getByRole('menuitem', { name: 'Receive line item' }).click();

  // Select destination location
  await page.getByLabel('related-field-location').click();
  await page.getByRole('option', { name: 'Factory', exact: true }).click();

  // Receive only a *single* item
  await page.getByLabel('number-field-quantity').fill('1');

  // Assign custom information
  await page.getByLabel('action-button-assign-batch-').click();
  await page.getByLabel('action-button-adjust-packaging').click();
  await page.getByLabel('action-button-change-status').click();
  await page.getByLabel('action-button-add-note').click();

  await page
    .getByLabel('text-field-batch_code', { exact: true })
    .fill('my-batch-code');
  await page.getByLabel('text-field-packaging', { exact: true }).fill('bucket');
  await page
    .getByLabel('text-field-note', { exact: true })
    .fill('The quick brown fox');
  await page.getByLabel('choice-field-status').click();
  await page.getByRole('option', { name: 'Destroyed' }).click();

  // Short timeout to allow for debouncing
  await page.waitForTimeout(200);

  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Items received').waitFor();

  await loadTab(page, 'Received Stock');
  await clearTableFilters(page);

  await page.getByRole('cell', { name: 'my-batch-code' }).first().waitFor();
});

test('Purchase Orders - Duplicate', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'purchasing/purchase-order/13/detail'
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
});
