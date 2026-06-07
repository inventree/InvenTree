import { expect, test } from '../baseFixtures.js';
import { stevenuser } from '../defaults.js';
import {
  activateCalendarView,
  clearTableFilters,
  clickButtonIfVisible,
  clickOnRowMenu,
  loadTab,
  navigate,
  openFilterDrawer,
  setTableChoiceFilter
} from '../helpers.js';
import { doCachedLogin } from '../login.js';

test('Stock - Basic Tests', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'stock/location/index/' });

  await page.waitForURL('**/web/stock/location/**');

  await loadTab(page, 'Stock Items');
  await page.getByText('1551ABK').first().click();

  await page.getByRole('tab', { name: 'Stock', exact: true }).click();
  await page.waitForURL('**/web/stock/**');
  await loadTab(page, 'Stock Locations');
  await page.getByRole('cell', { name: 'Electronics Lab' }).first().click();
  await loadTab(page, 'Default Parts');
  await loadTab(page, 'Sublocations');
  await loadTab(page, 'Stock Items');
  await loadTab(page, 'Location Details');

  await navigate(page, 'stock/item/1194/details');
  await page.getByText('D.123 | Doohickey').waitFor();
  await page.getByText('Batch Code: BX-123-2024-2-7').waitFor();
  await loadTab(page, 'Stock Tracking');
  await loadTab(page, 'Test Results');
  await page.getByText('395c6d5586e5fb656901d047be27e1f7').waitFor();
  await loadTab(page, 'Installed Items');

  // Let's create a new stock item
  await navigate(page, 'part/822/stock');
  await page
    .getByRole('button', { name: 'action-button-add-stock-item' })
    .click();
  await page
    .getByRole('textbox', { name: 'number-field-quantity' })
    .fill('987');
  await page.getByRole('button', { name: 'Submit' }).click();

  // Automatically navigate through to the newly created stock item
  await page.getByText('Quantity: 987').first().waitFor();
  await loadTab(page, 'Stock Tracking');
  await page
    .getByRole('cell', { name: 'Stock item created' })
    .first()
    .waitFor();
  await page.getByRole('cell', { name: 'allaccess Ally Access' }).waitFor();
});

test('Stock - Location Tree', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'stock/location/index/' });

  await page.waitForURL('**/web/stock/location/**');

  await page.getByLabel('nav-breadcrumb-action').click();
  await page.getByLabel('nav-tree-toggle-1}').click();
  await page.getByLabel('nav-tree-item-2').click();

  await page.getByLabel('breadcrumb-2-storage-room-a').waitFor();
  await page.getByLabel('breadcrumb-1-factory').click();

  await page.getByRole('cell', { name: 'Factory' }).first().waitFor();
});

test('Stock - Location Delete', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'stock/location/38/sublocations'
  });

  const loc_1 = `loc-1-${Math.floor(Math.random() * 1000)}`;
  const loc_2 = `loc-2-${Math.floor(Math.random() * 1000)}`;

  // Create a sub-location
  await page
    .getByRole('button', { name: 'action-button-add-stock-location' })
    .click();
  await page.getByRole('textbox', { name: 'text-field-name' }).fill(loc_1);
  await page.getByRole('button', { name: 'Submit' }).click();

  // Create a secondary sub-location
  await loadTab(page, 'Sublocations');
  await page
    .getByRole('button', { name: 'action-button-add-stock-location' })
    .click();
  await page.getByRole('textbox', { name: 'text-field-name' }).fill(loc_2);
  await page.getByRole('button', { name: 'Submit' }).click();

  // Navigate up to parent
  await page.getByRole('link', { name: `breadcrumb-2-${loc_1}` }).click();
  await loadTab(page, 'Sublocations');
  await page.getByRole('cell', { name: loc_2, exact: true }).waitFor();

  // Delete this location, and all child locations
  await page
    .getByRole('button', { name: 'action-menu-location-actions' })
    .first()
    .click();
  await page
    .getByRole('menuitem', { name: 'action-menu-location-actions-delete' })
    .click();

  await page
    .getByRole('combobox', { name: 'choice-field-delete_stock_items' })
    .click();
  await page
    .getByRole('option', { name: 'Move items to parent location' })
    .click();

  await page
    .getByRole('combobox', { name: 'choice-field-delete_sub_locations' })
    .click();
  await page.getByRole('option', { name: 'Delete items' }).click();

  await page.getByRole('button', { name: 'Delete' }).click();

  // Confirm we are on the right page
  await page.getByText('External PCB assembler').waitFor();
  await loadTab(page, 'Sublocations');
  await page.getByText('No records found').first().waitFor();
});

test('Stock - Filters', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    user: stevenuser,
    url: '/stock/location/index/'
  });

  await loadTab(page, 'Stock Items');

  await openFilterDrawer(page);
  await clickButtonIfVisible(page, 'Clear Filters');

  // Filter by updated date
  await page.getByRole('button', { name: 'Add Filter' }).click();
  await page.getByPlaceholder('Select filter').fill('updated');
  await page.getByText('Updated After').click();
  await page.getByPlaceholder('Select date value').fill('2010-01-01');
  await page.getByText('Show items updated after this date').waitFor();

  // Filter by batch code
  await page.getByRole('button', { name: 'Add Filter' }).click();
  await page.getByPlaceholder('Select filter').fill('batch');
  await page
    .getByRole('option', { name: 'Batch Code', exact: true })
    .locator('span')
    .click();
  await page.getByPlaceholder('Enter filter value').fill('TABLE-B02');
  await page.getByLabel('apply-text-filter').click();

  // Close dialog
  await page.keyboard.press('Escape');

  // Ensure correct result is displayed
  await page
    .getByRole('cell', { name: 'A round table - with blue paint' })
    .waitFor();

  // Filter by custom status code
  await clearTableFilters(page);
  await setTableChoiceFilter(page, 'Status', 'Incoming goods inspection');
  await page.getByRole('cell', { name: '1551AGY' }).first().waitFor();

  await page.getByPlaceholder('Search').clear();
  await page.getByPlaceholder('Search').fill('blue');
  await page.getByRole('cell', { name: 'widget.blue' }).first().waitFor();

  await page.getByPlaceholder('Search').clear();
  await page.getByPlaceholder('Search').fill('002.01');
  await page.getByRole('cell', { name: '002.01-PCBA' }).first().waitFor();

  await clearTableFilters(page);
});

test('Stock - Serial Numbers', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  // Use the "global search" functionality to find a part we are interested in
  // This is to exercise the search functionality and ensure it is working as expected
  await page.getByLabel('open-search').click();

  await page.getByLabel('global-search-input').clear();

  await page.waitForTimeout(250);
  await page.getByLabel('global-search-input').fill('widget green');
  await page.waitForTimeout(250);

  // Remove the "stock item" results group
  await page.getByLabel('remove-search-group-stockitem').click();

  await page
    .getByText(/widget\.green/)
    .first()
    .click();

  await page
    .getByLabel('panel-tabs-part')
    .getByRole('tab', { name: 'Stock', exact: true })
    .click();
  await page.getByLabel('action-button-add-stock-item').click();

  // Initially fill with invalid serial/quantity combinations
  await page
    .getByLabel('text-field-serial_numbers', { exact: true })
    .fill('200-250');
  await page.getByLabel('number-field-quantity').fill('10');

  // Add delay to account to field debounce
  await page.waitForTimeout(250);

  await page.getByRole('button', { name: 'Submit' }).click();

  // Expected error messages
  await page.getByText('Errors exist for one or more form fields').waitFor();
  await page
    .getByText(/exceeds allowed quantity/)
    .first()
    .waitFor();

  // Now, with correct quantity
  await page.getByLabel('number-field-quantity').fill('51');
  await page.waitForTimeout(250);
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.waitForTimeout(250);

  await page
    .getByText(
      /The following serial numbers already exist or are invalid : 200,201,202,203,204/
    )
    .first()
    .waitFor();

  // Expected error messages
  await page.getByText('Errors exist for one or more form fields').waitFor();

  // Close the form
  await page.getByRole('button', { name: 'Cancel' }).click();
});

// Test navigation by serial number
test('Stock - Serial Navigation', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'part/79/details' });

  await page.getByLabel('action-menu-stock-actions').click();
  await page.getByLabel('action-menu-stock-actions-search').click();
  await page.getByLabel('text-field-serial', { exact: true }).fill('359');
  await page.getByRole('button', { name: 'Submit' }).click();

  // Start at serial 359
  await page.getByText('359', { exact: true }).first().waitFor();
  await page.getByLabel('next-serial-number').waitFor();
  await page.getByLabel('previous-serial-number').click();

  // Navigate to serial 358
  await page.getByText('358', { exact: true }).first().waitFor();

  await page.getByLabel('action-button-find-serial').click();
  await page.getByLabel('text-field-serial', { exact: true }).fill('200');
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.getByText('Serial Number: 200').waitFor();
  await page.getByText('200', { exact: true }).first().waitFor();
  await page.getByText('199', { exact: true }).first().waitFor();
  await page.getByText('201', { exact: true }).first().waitFor();
});

test('Stock - Serialize', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'stock/item/232/details' });

  // Fill out with faulty serial numbers to check buttons and forms
  await page.getByLabel('action-menu-stock-operations').click();
  await page.getByLabel('action-menu-stock-operations-serialize').click();

  // Check for expected placeholder value
  await expect(
    page.getByRole('textbox', {
      name: 'text-field-serial_numbers',
      exact: true
    })
  ).toHaveAttribute('placeholder', '365+');

  await page
    .getByLabel('text-field-serial_numbers', { exact: true })
    .fill('200-250');

  await page.getByRole('button', { name: 'Submit' }).click();

  await page
    .getByText('Number of unique serial numbers (51) must match quantity (100)')
    .waitFor();

  await page
    .getByLabel('text-field-serial_numbers', { exact: true })
    .fill('1, 2, 3');
  await page.waitForTimeout(250);
  await page.getByRole('button', { name: 'Submit' }).click();

  await page
    .getByText('Number of unique serial numbers (3) must match quantity (100)')
    .waitFor();

  await page.getByRole('button', { name: 'Cancel' }).click();
});

/**
 * Test various 'actions' on the stock detail page
 */
test('Stock - Stock Actions', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'stock/item/1225/details' });

  // Helper function to launch a stock action
  const launchStockAction = async (action: string) => {
    await page.getByLabel('action-menu-stock-operations').click();
    await page.getByLabel(`action-menu-stock-operations-${action}`).click();
  };

  const setStockStatus = async (status: string) => {
    await page.getByLabel('action-button-change-status').click();
    await page.getByLabel('choice-field-status').click();
    await page.getByRole('option', { name: status }).click();
  };

  // Duplicate the stock item first - prevent impacting other tests
  await page
    .getByRole('button', { name: 'action-menu-stock-item-actions' })
    .click();
  await page
    .getByRole('menuitem', { name: 'action-menu-stock-item-actions-duplicate' })
    .click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.waitForLoadState('networkidle');

  // Check for required values
  await page.getByText('Status', { exact: true }).waitFor();
  await page.getByText('Custom Status', { exact: true }).waitFor();
  await page.getByText('Attention needed').first().waitFor();
  await page
    .getByLabel('Stock Details')
    .getByText('Incoming goods inspection')
    .waitFor();
  await page.getByText('123').first().waitFor();

  // Check barcode actions
  await page.getByLabel('action-menu-barcode-actions').click();
  await page
    .getByLabel('action-menu-barcode-actions-scan-into-location')
    .click();
  await page
    .getByPlaceholder('Enter barcode data')
    .fill('{"stocklocation": 12}');
  await page.getByRole('button', { name: 'Scan', exact: true }).click();
  await page.getByText('Scanned stock item into location').waitFor();

  // Add "zero" stock - ensure the quantity stays the same
  await launchStockAction('add');
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Quantity: 123').first().waitFor();

  // Add stock, and change status
  await launchStockAction('add');
  await page.getByLabel('number-field-quantity').fill('12');
  await setStockStatus('Lost');
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.getByText('Lost').first().waitFor();
  await page.getByText('Unavailable').first().waitFor();
  await page.getByText('135').first().waitFor();

  // Remove "zero" stock - ensure the quantity stays the same
  await launchStockAction('remove');
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Quantity: 135').first().waitFor();

  // Remove stock, and change status
  await launchStockAction('remove');
  await page.getByLabel('number-field-quantity').fill('99');
  await setStockStatus('Damaged');
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.getByText('36').first().waitFor();
  await page.getByText('Damaged').first().waitFor();

  // Count stock and change status (reverting to original value)
  await launchStockAction('count');
  await page.getByLabel('number-field-quantity').fill('123');
  await setStockStatus('Incoming goods inspection');
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.getByText('123').first().waitFor();
  await page.getByText('Custom Status').first().waitFor();
  await page.getByText('Incoming goods inspection').first().waitFor();

  // Find an item which has been sent to a customer
  await navigate(page, 'stock/item/1014/details');
  await page.getByText('Batch Code: 2022-11-12').waitFor();
  await page.getByText('Unavailable').waitFor();
  await page.getByLabel('action-menu-stock-operations').click();
  await page.getByLabel('action-menu-stock-operations-return').click();
});

// Test conversion between part variants
test('Stock - Convert', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'stock/item/242/details' });

  await page.getByText('widget.red.00 | Red Widget |').waitFor();

  // Convert to widget.red.02
  await page
    .getByRole('button', { name: 'action-menu-stock-item-actions' })
    .click();
  await page
    .getByRole('menuitem', { name: 'action-menu-stock-item-actions-convert' })
    .click();
  await page.getByRole('combobox', { name: 'related-field-part' }).fill('red');
  await page.getByText('widget.red.02 | Red Widget |').click();
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.getByText('widget.red.02 | Red Widget |').waitFor();

  // Convert to widget.red.00
  await page
    .getByRole('button', { name: 'action-menu-stock-item-actions' })
    .click();
  await page
    .getByRole('menuitem', { name: 'action-menu-stock-item-actions-convert' })
    .click();
  await page.getByRole('combobox', { name: 'related-field-part' }).fill('red');
  await page.getByText('widget.red.00 | Red Widget |').click();
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.getByText('widget.red.00 | Red Widget |').waitFor();
});

test('Stock - Return Items', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'sales/customer/32/assigned-stock'
  });

  // Return stock items assigned to customer
  await page.getByRole('checkbox', { name: 'Select all records' }).check();
  await page.getByRole('button', { name: 'action-menu-stock-actions' }).click();
  await page
    .getByRole('menuitem', { name: 'action-menu-stock-actions-return-stock' })
    .click();
  await page.getByText('Return selected items into stock').first().waitFor();
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Location detail
  await navigate(page, 'stock/item/1253');
  await page
    .getByRole('button', { name: 'action-menu-stock-operations' })
    .click();
  await page
    .getByRole('menuitem', {
      name: 'action-menu-stock-operations-return-stock'
    })
    .click();

  await page.getByText('#128').waitFor();
  await page.getByText('Merge into existing stock').waitFor();
  await page.getByRole('textbox', { name: 'number-field-quantity' }).fill('0');
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.getByText('Quantity must be greater than zero').waitFor();
  await page.getByText('This field is required.').waitFor();
});

test('Stock - Tracking', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'stock/item/176/details' });

  await page.getByRole('link', { name: 'Widget Assembly # 2' }).waitFor();

  // Navigate to the "stock tracking" tab
  await loadTab(page, 'Stock Tracking');
  await page.getByText('- - Factory/Office Block/Room').first().waitFor();
  await page.getByRole('link', { name: 'Widget Assembly' }).waitFor();
  await page.getByRole('cell', { name: 'Installed into assembly' }).waitFor();

  /* Add some more stock items and tracking information:
   * - Duplicate this stock item
   * - Give it a unique serial number
   * - Ensure the tracking information is duplicated correctly
   * - Delete the new stock item
   * - Ensure that the tracking information is retained against the base part
   */

  // Duplicate the stock item
  await page
    .getByRole('button', { name: 'action-menu-stock-item-actions' })
    .click();
  await page
    .getByRole('menuitem', { name: 'action-menu-stock-item-actions-duplicate' })
    .click();
  await page
    .getByRole('textbox', { name: 'text-field-serial_numbers' })
    .fill('9876');
  await page.getByRole('button', { name: 'Submit' }).click();

  // Check stock tracking information is correct
  await page.getByText('Serial Number: 9876').first().waitFor();
  await loadTab(page, 'Stock Tracking');
  await page
    .getByRole('cell', { name: 'Stock item created' })
    .first()
    .waitFor();

  // Delete this stock item
  await page
    .getByRole('button', { name: 'action-menu-stock-item-actions' })
    .click();
  await page
    .getByRole('menuitem', { name: 'action-menu-stock-item-actions-delete' })
    .click();
  await page.getByRole('button', { name: 'Delete' }).click();

  // Check stock tracking for base part
  await loadTab(page, 'Stock History');
  await page.getByRole('button', { name: 'Stock Tracking' }).click();

  await page.getByText('Stock item no longer exists').first().waitFor();
  await page
    .getByRole('cell', { name: 'Thumbnail Blue Widget' })
    .first()
    .waitFor();

  await page.getByText('# 162').first().waitFor();
});

test('Stock - Location', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'stock/location/12/' });

  await loadTab(page, 'Default Parts');
  await loadTab(page, 'Stock Items');
  await loadTab(page, 'Sublocations');
  await loadTab(page, 'Location Details');

  await page.getByLabel('action-menu-barcode-actions').click();
  await page
    .getByLabel('action-menu-barcode-actions-scan-in-stock-items')
    .waitFor();
  await page
    .getByLabel('action-menu-barcode-actions-scan-in-container')
    .click();

  // Attempt to scan in the same location (should fail)
  await page
    .getByPlaceholder('Enter barcode data')
    .fill('{"stocklocation": 12}');
  await page.getByRole('button', { name: 'Scan', exact: true }).click();
  await page.getByText('Error scanning stock location').waitFor();

  // Attempt to scan bad data (no match)
  await page
    .getByPlaceholder('Enter barcode data')
    .fill('{"stocklocation": 1234}');
  await page.getByRole('button', { name: 'Scan', exact: true }).click();
  await page.getByText('No match found for barcode data').waitFor();
});

test('Transfer Orders - General', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  await page.getByRole('tab', { name: 'Stock' }).click();
  await page.waitForURL('**/stock/location/index/**');

  await loadTab(page, 'Transfer Orders');

  await clearTableFilters(page);

  // We have now loaded the "Transfer Orders" table. Check for some expected texts
  await page.getByText('Complete').first().waitFor();
  await page.getByText('Issued').first().waitFor();
  await page.getByText('Cancelled').first().waitFor();

  // Load a particular Transfer Order
  await page.getByRole('cell', { name: 'TO-0002' }).click();
  await page.waitForTimeout(200);

  // This transfer order should be "issued"
  await page.getByText('Issued').first().waitFor();

  // Edit the transfer order (via keyboard shortcut)
  await page.keyboard.press('Control+E');
  await page.getByLabel('text-field-reference', { exact: true }).waitFor();
  await page.getByLabel('related-field-project_code').waitFor();
  await page.getByRole('button', { name: 'Cancel' }).click();

  await page.getByRole('button', { name: 'Complete Order' }).click();
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Check for other expected actions
  await page.getByRole('button', { name: 'action-menu-order-actions' }).click();
  await page.getByLabel('action-menu-order-actions-edit').waitFor();
  await page.getByLabel('action-menu-order-actions-duplicate').waitFor();
  await page.getByLabel('action-menu-order-actions-hold').waitFor();

  // Click on some tabs
  await loadTab(page, 'Line Items');
  await loadTab(page, 'Allocated Stock');
  await loadTab(page, 'Parameters');
  await loadTab(page, 'Attachments');
  await loadTab(page, 'Notes');
});

test('Transfer Order - Reference', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  // go to transfer orders
  await page.getByRole('tab', { name: 'Stock' }).click();
  await page.waitForURL('**/stock/location/index/**');
  await loadTab(page, 'Transfer Orders');

  // click add button
  await page
    .getByRole('button', { name: 'action-button-add-transfer-' })
    .click();

  // Ensure a new reference is suggested
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(250);

  // Grab the Transfer Order reference
  const reference: string = await page
    .getByRole('textbox', { name: 'text-field-reference' })
    .inputValue();
  expect(reference).toMatch(/TO-\d+/);

  await page.getByRole('textbox', { name: 'text-field-description' }).click();
  await page
    .getByRole('textbox', { name: 'text-field-description' })
    .fill('creating from playwrigh!');

  // create the transfer order
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Item Created').waitFor();

  // go back to stock page
  await page.getByRole('link', { name: 'Stock', exact: true }).click();
  await page
    .getByRole('button', { name: 'action-button-add-transfer-' })
    .click();

  const nextReference: string = await page
    .getByRole('textbox', { name: 'text-field-reference' })
    .inputValue();
  expect(nextReference).toMatch(/TO-\d+/);

  // Ensure that the reference has incremented
  const refNumber = Number(reference.replace('TO-', ''));
  const nextRefNumber = Number(nextReference.replace('TO-', ''));
  expect(nextRefNumber).toBe(refNumber + 1);
});

test('Transfer Order - Calendar', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  await navigate(page, 'stock/location/index/transfer-orders');
  await activateCalendarView(page);

  // Export calendar data
  await page.getByLabel('calendar-export-data').click();
  await page.getByRole('button', { name: 'Export', exact: true }).click();
  await page.getByText('Process completed successfully').waitFor();

  // Required because we downloaded a file
  await page.context().close();
});

test('Transfer Order - Edit', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  await navigate(page, 'stock/transfer-order/2/');

  // Check for expected text items
  await page.getByText('Consume some paint').first().waitFor();
  await page.getByText('2026-04-20').waitFor(); // Created date
  await page.getByText('2026-04-23').waitFor(); // Issue date
  await page.getByText('PRJ-HEL').waitFor(); // Project Code

  await page.keyboard.press('Control+E');

  // Edit start date
  await page.getByLabel('date-field-start_date').fill('2026-04-28');

  // Submit the form
  await page.getByRole('button', { name: 'Submit' }).click();

  // Expect error
  await page.getByText('Errors exist for one or more form fields').waitFor();
  await page.getByText('Target date must be after start date').waitFor();

  // Cancel the form
  await page.getByRole('button', { name: 'Cancel' }).click();
});

test('Transfer Order - Allocate and Transfer', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  await navigate(page, 'stock/transfer-order/6/');

  // Duplicate this transfer order, to ensure a fresh run each time
  await page.getByLabel('action-menu-order-actions').click();
  await page.getByLabel('action-menu-order-actions-duplicate').click();

  // Submit the duplicate request and ensure it completes
  await page.getByRole('button', { name: 'Submit' }).isEnabled();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Item Created').waitFor();

  // Issue the order
  await page.getByRole('button', { name: 'Issue Order' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Issued', { exact: true }).first().waitFor();

  await loadTab(page, 'Line Items');

  // Allocate line item 1
  const cell1 = await page.getByText('C_100pF_0402', { exact: true });
  await clickOnRowMenu(cell1);
  await page.getByRole('menuitem', { name: 'Allocate Stock' }).click();
  await page.getByText('C_100pF_0402Location:Offsite').waitFor();
  await page.waitForTimeout(200);
  await page.getByRole('button', { name: 'Submit' }).click();

  // Allocate line item 1
  const cell2 = await page.getByText('R_2.2K_0603_1%', { exact: true });
  await clickOnRowMenu(cell2);
  await page.getByRole('menuitem', { name: 'Allocate Stock' }).click();
  await page.getByText('R_2.2K_0603_1%Location:').waitFor();
  await page.waitForTimeout(200);
  await page.getByRole('button', { name: 'Submit' }).click();

  // Complete the order
  await page.getByRole('button', { name: 'Complete Order' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Complete', { exact: true }).first().waitFor();

  // Tab should have changed to Transferred Stock
  await loadTab(page, 'Transferred Stock');
  await page.getByText('C_100pF_0402').waitFor();
  await page.getByText('2.2K resistor in 0603 SMD').waitFor();
});

test('Transfer Orders - Duplicate', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'stock/transfer-order/1/detail'
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
