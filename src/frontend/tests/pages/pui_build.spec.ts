import { expect } from '@playwright/test';
import { test } from '../baseFixtures.ts';
import {
  activateCalendarView,
  clearTableFilters,
  clickOnRowMenu,
  getRowFromCell,
  loadTab,
  navigate,
  setTableChoiceFilter
} from '../helpers.ts';
import { doCachedLogin } from '../login.ts';

test('Build - Index', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'manufacturing/index/' });

  await loadTab(page, 'Build Orders');

  // Ensure all data views are available
  await page
    .getByRole('button', { name: 'segmented-icon-control-parametric' })
    .click();

  await page
    .getByRole('button', { name: 'segmented-icon-control-calendar' })
    .click();
  await page.getByRole('button', { name: 'action-button-next-month' }).click();

  await page
    .getByRole('button', { name: 'segmented-icon-control-table' })
    .click();
});

test('Build Order - Basic Tests', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  // Navigate to the correct build order
  await page.getByRole('tab', { name: 'Manufacturing' }).click();
  await page.waitForURL('**/manufacturing/index/**');

  await loadTab(page, 'Build Orders');

  await clearTableFilters(page);

  // We have now loaded the "Build Order" table. Check for some expected texts
  await page.getByText('On Hold').first().waitFor();
  await page.getByText('Pending').first().waitFor();

  // Load a particular build order
  await page.getByRole('cell', { name: 'BO0017' }).click();

  // This build order should be "on hold"
  await page.getByText('On Hold').first().waitFor();

  // Edit the build order (via keyboard shortcut)
  await page.keyboard.press('Control+E');
  await page.getByLabel('text-field-title', { exact: true }).waitFor();
  await page.getByLabel('related-field-project_code').waitFor();
  await page.getByRole('button', { name: 'Cancel' }).click();

  await page.getByRole('button', { name: 'Issue Order' }).click();
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Back to the build list
  await page.getByLabel('breadcrumb-0-manufacturing').click();

  // Load a different build order
  await page.getByRole('cell', { name: 'BO0011' }).click();

  // This build order should be "in production"
  await page.getByText('Production').first().waitFor();
  await page.getByRole('button', { name: 'Complete Order' }).click();
  await page.getByText('Accept Unallocated').waitFor();
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Check for other expected actions
  await page.getByLabel('action-menu-build-order-').click();
  await page.getByLabel('action-menu-build-order-actions-edit').waitFor();
  await page.getByLabel('action-menu-build-order-actions-duplicate').waitFor();
  await page.getByLabel('action-menu-build-order-actions-hold').waitFor();
  await page.getByLabel('action-menu-build-order-actions-cancel').click();
  await page.getByText('Remove Incomplete Outputs').waitFor();
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Click on some tabs
  await loadTab(page, 'Attachments');
  await loadTab(page, 'Notes');
  await loadTab(page, 'Incomplete Outputs');
  await loadTab(page, 'Required Parts');
  await loadTab(page, 'Allocated Stock');

  // Check for expected text in the table
  await page.getByText('R_10R_0402_1%').waitFor();
  await page
    .getByRole('cell', { name: 'R38, R39, R40, R41, R42, R43' })
    .waitFor();

  // Check "test results"
  await loadTab(page, 'Test Results');
  await page.getByText('Quantity: 25').waitFor();
  await page.getByText('Continuity Checks').waitFor();

  const button = await page
    .getByRole('row', { name: 'Quantity: 16' })
    .getByLabel('add-test-result');

  await button.click();
  await page
    .getByRole('textbox', { name: 'text-field-value', exact: true })
    .waitFor();
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Click through to the "parent" build
  await loadTab(page, 'Build Details');
  await page.getByRole('link', { name: 'BO0010' }).click();
  await page
    .getByLabel('Build Details')
    .getByText('Making a high level assembly')
    .waitFor();
});

// Test that the build order reference field increments correctly
test('Build Order - Reference', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'manufacturing/index/buildorders'
  });

  await page
    .getByRole('button', { name: 'action-button-add-build-order' })
    .click();
  await page.getByRole('button', { name: 'Submit' }).waitFor();

  // Grab the next BuildOrder reference
  const reference: string = await page
    .getByRole('textbox', { name: 'text-field-reference' })
    .inputValue();
  expect(reference).toMatch(/BO\d+/);

  // Select a part
  await page.getByLabel('related-field-part').fill('MAST');
  await page.getByText('MAST | Master Assembly').click();

  // Submit the form
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Item Created').waitFor();

  // Back to the "build order" page - to create a new order
  await navigate(page, 'manufacturing/index/buildorders');

  await page
    .getByRole('button', { name: 'action-button-add-build-order' })
    .click();
  await page.getByRole('button', { name: 'Submit' }).waitFor();

  const nextReference: string = await page
    .getByRole('textbox', { name: 'text-field-reference' })
    .inputValue();
  expect(nextReference).toMatch(/BO\d+/);

  // Ensure that the reference has incremented
  const refNumber = Number(reference.replace('BO', ''));
  const nextRefNumber = Number(nextReference.replace('BO', ''));
  expect(nextRefNumber).toBe(refNumber + 1);
});

test('Build Order - Calendar', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  await navigate(page, 'manufacturing/index/buildorders');
  await activateCalendarView(page);

  // Export calendar data
  await page.getByLabel('calendar-export-data').click();
  await page.getByRole('button', { name: 'Export', exact: true }).click();
  await page.getByText('Process completed successfully').waitFor();

  // Check "part category" filter
  await page.getByLabel('calendar-select-filters').click();
  await page.getByRole('button', { name: 'Add Filter' }).click();
  await page.getByPlaceholder('Select filter').fill('category');
  await page
    .getByRole('option', { name: 'Part Category', exact: true })
    .click();
  await page.getByLabel('related-field-filter-category').click();
  await page.getByText('Part category, level 1').waitFor();

  // Required because we downloaded a file
  await page.context().close();
});

test('Build Order - Edit', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  await navigate(page, 'manufacturing/build-order/22/');

  // Check for expected text items
  await page.getByText('Building for sales order').first().waitFor();
  await page.getByText('2024-08-08').waitFor(); // Created date
  await page.getByText('2025-01-01').waitFor(); // Start date
  await page.getByText('2025-01-22').waitFor(); // Target date

  await page.keyboard.press('Control+E');

  // Edit start date
  await page.getByLabel('date-field-start_date').fill('2026-09-09');

  // Submit the form
  await page.getByRole('button', { name: 'Submit' }).click();

  // Expect error
  await page.getByText('Errors exist for one or more form fields').waitFor();
  await page.getByText('Target date must be after start date').waitFor();

  // Cancel the form
  await page.getByRole('button', { name: 'Cancel' }).click();
});

test('Build Order - Build Outputs', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  await navigate(page, 'manufacturing/index/');
  await loadTab(page, 'Build Orders');

  await clearTableFilters(page);

  // We have now loaded the "Build Order" table. Check for some expected texts
  await page.getByText('On Hold').first().waitFor();
  await page.getByText('Pending').first().waitFor();

  await page.getByRole('cell', { name: 'BO0011' }).click();
  await loadTab(page, 'Incomplete Outputs');

  // Check the "printing" actions for the selected outputs
  await page.getByRole('checkbox', { name: 'Select all records' }).click();
  await page
    .getByRole('tabpanel', { name: 'Incomplete Outputs' })
    .getByLabel('action-menu-printing-actions')
    .click();
  await page
    .getByRole('menuitem', {
      name: 'action-menu-printing-actions-print-labels'
    })
    .waitFor();
  await page
    .getByRole('menuitem', {
      name: 'action-menu-printing-actions-print-reports'
    })
    .click();
  await page.getByRole('button', { name: 'Print', exact: true }).click();
  await page.getByText('Errors exist for one or more form fields').waitFor();
  await page.getByRole('button', { name: 'Cancel', exact: true }).click();
  await page.getByRole('checkbox', { name: 'Select all records' }).click();

  // Create a new build output
  await page.getByLabel('action-button-add-build-output').click();
  await page.getByLabel('number-field-quantity').fill('5');

  const placeholder: string =
    (await page
      .getByLabel('text-field-serial_numbers', { exact: true })
      .getAttribute('placeholder')) || '';

  expect(placeholder).toContain('+');

  let sn = 1;

  sn = Number.parseInt(placeholder.split('+')[0].trim());

  // Generate some new serial numbers
  await page
    .getByLabel('text-field-serial_numbers', { exact: true })
    .fill(`${sn}, ${sn + 1}`);

  // Accept the suggested batch code
  await page
    .getByRole('img', { name: 'field-batch_code-accept-placeholder' })
    .click();

  await page.getByLabel('related-field-location').click();
  await page.getByLabel('related-field-location').fill('Reel');
  await page.getByText('- Electronics Lab/Reel Storage').click();
  await page.getByRole('button', { name: 'Submit' }).click();

  // Should be an error as the number of serial numbers doesn't match the quantity
  await page.getByText('Errors exist for one or more').waitFor();
  await page.getByText('Number of unique serial').waitFor();

  // Fix the quantity
  await page.getByLabel('number-field-quantity').fill('2');
  await page.waitForTimeout(250);
  await page.getByRole('button', { name: 'Submit' }).click();

  // Check that new serial numbers have been created
  await page
    .getByRole('cell', { name: `# ${sn}` })
    .first()
    .waitFor();
  await page
    .getByRole('cell', { name: `# ${sn + 1}` })
    .first()
    .waitFor();

  // Cancel one of the newly created outputs
  const cell = await page.getByRole('cell', { name: `# ${sn}` });
  const row = await getRowFromCell(cell);
  await row.getByLabel(/row-action-menu-/i).click();
  await page.getByRole('menuitem', { name: 'Cancel' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Build outputs have been cancelled').waitFor();

  // Complete the other output
  const cell2 = await page.getByRole('cell', { name: `# ${sn + 1}` });
  const row2 = await getRowFromCell(cell2);
  await row2.getByLabel(/row-action-menu-/i).click();
  await page.getByRole('menuitem', { name: 'Complete' }).click();
  await page.getByLabel('related-field-location').click();
  await page.getByText('Mechanical Lab').click();
  await page.waitForTimeout(250);
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Build outputs have been completed').waitFor();

  // Check for expected UI elements in the "scrap output" dialog
  const cell3 = await page.getByRole('cell', { name: '16' });
  const row3 = await getRowFromCell(cell3);
  await row3.getByLabel(/row-action-menu-/i).click();
  await page.getByRole('menuitem', { name: 'Scrap' }).click();

  await page
    .getByText(
      'Selected build outputs will be completed, but marked as scrapped'
    )
    .waitFor();
  await page.getByRole('cell', { name: 'Quantity: 16' }).waitFor();
  await page.getByRole('button', { name: 'Cancel', exact: true }).click();
});

test('Build Order - Allocation', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  await navigate(page, 'manufacturing/build-order/1/line-items');

  // Expand the R_10K_0805 line item
  await page.getByText('R_10K_0805_1%').first().click();
  await page.getByText('Reel Storage').waitFor();
  await page.getByText('R_10K_0805_1%').first().click();

  await page.reload();

  // The capacitor stock should be fully allocated
  const cell = await page.getByRole('cell', { name: /C_1uF_0805/ });
  const row = await getRowFromCell(cell);

  await row.getByText(/150 \/ 150/).waitFor();

  // Expand this row
  await cell.click();
  await page.getByRole('cell', { name: '2022-4-27', exact: true }).waitFor();
  await page.getByRole('cell', { name: 'Reel Storage', exact: true }).waitFor();

  // Navigate to the "Incomplete Outputs" tab
  await loadTab(page, 'Incomplete Outputs');

  // Find output #7
  const output7 = await page
    .getByRole('cell', { name: '# 7' })
    .locator('xpath=ancestor::tr')
    .first();

  // Expecting 3/4 allocated outputs
  await output7.getByText('3 / 4').waitFor();

  // Expecting 0/3 completed tests
  await output7.getByText('0 / 3').waitFor();

  // Expand the output
  await output7.click();

  await page.getByText('Build Output Stock Allocation').waitFor();
  await page.getByText('Serial Number: 7').waitFor();

  // Data of expected rows
  const data = [
    {
      name: 'Red Widget',
      ipn: 'widget.red',
      available: '123',
      required: '3',
      allocated: '3'
    },
    {
      name: 'Blue Widget',
      ipn: 'widget.blue',
      available: '129',
      required: '5',
      allocated: '5'
    },
    {
      name: 'Pink Widget',
      ipn: 'widget.pink',
      available: '4',
      required: '4',
      allocated: '0'
    },
    {
      name: 'Green Widget',
      ipn: 'widget.green',
      available: '245',
      required: '6',
      allocated: '6'
    }
  ];

  // Check for expected rows
  for (let idx = 0; idx < data.length; idx++) {
    const item = data[idx];

    const cell = await page.getByRole('cell', { name: item.name });
    const row = await getRowFromCell(cell);
    const progress = `${item.allocated} / ${item.required}`;

    await row.getByRole('cell', { name: item.ipn }).first().waitFor();
    await row.getByRole('cell', { name: item.available }).first().waitFor();
    await row.getByRole('cell', { name: progress }).first().waitFor();
  }

  // Check for expected buttons on Red Widget
  const redWidget = await page.getByRole('cell', { name: 'Red Widget' });
  const redRow = await getRowFromCell(redWidget);

  await redRow.getByLabel(/row-action-menu-/i).click();
  await page
    .getByRole('menuitem', { name: 'Allocate Stock', exact: true })
    .waitFor();
  await page
    .getByRole('menuitem', { name: 'Deallocate Stock', exact: true })
    .waitFor();
});

// Test partial stock consumption against build order
test('Build Order - Consume Stock', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'manufacturing/build-order/24/line-items'
  });

  // Check for expected progress values
  await page.getByText('2 / 2', { exact: true }).waitFor();
  await page.getByText('8 / 10', { exact: true }).waitFor();
  await page.getByText('5 / 35', { exact: true }).waitFor();
  await page.getByText('5 / 40', { exact: true }).waitFor();

  // Open the "Allocate Stock" dialog
  await page.getByRole('checkbox', { name: 'Select all records' }).click();
  await page
    .getByRole('button', { name: 'action-button-allocate-stock' })
    .click();
  await page
    .getByLabel('Allocate Stock')
    .getByText('5 / 35', { exact: true })
    .waitFor();
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Open the "Consume Stock" dialog
  await page
    .getByRole('button', { name: 'action-button-consume-stock' })
    .click();
  await page.getByLabel('Consume Stock').getByText('2 / 2').waitFor();
  await page.getByLabel('Consume Stock').getByText('8 / 10').waitFor();
  await page.getByLabel('Consume Stock').getByText('5 / 35').waitFor();
  await page.getByLabel('Consume Stock').getByText('5 / 40').waitFor();
  await page
    .getByRole('textbox', { name: 'text-field-notes', exact: true })
    .fill('some notes here...');
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Try with a different build order
  await navigate(page, 'manufacturing/build-order/26/line-items');
  await page.getByRole('checkbox', { name: 'Select all records' }).click();
  await page
    .getByRole('button', { name: 'action-button-consume-stock' })
    .click();

  await page.getByLabel('Consume Stock').getByText('306 / 1,900').waitFor();
  await page
    .getByLabel('Consume Stock')
    .getByText('Fully consumed')
    .first()
    .waitFor();

  await page.waitForTimeout(1000);
});

test('Build Order - Tracked Outputs', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'manufacturing/build-order/10/incomplete-outputs'
  });

  const cancelBuildOutput = async (cell) => {
    await clickOnRowMenu(cell);
    await page.getByRole('menuitem', { name: 'Cancel' }).click();
    await page.getByRole('button', { name: 'Submit', exact: true }).click();
    await page.getByText('Build outputs have been cancelled').waitFor();
  };

  // Ensure table has loaded
  await page.getByRole('cell', { name: '# 13' }).waitFor();

  // Check if the build output "#15" exists. If so, remove it.
  const existingCell = await page.getByRole('cell', { name: '# 15' });
  if (await existingCell.isVisible()) {
    await cancelBuildOutput(existingCell);
  }

  // Create a new build output, serial number 15
  await page
    .getByRole('button', { name: 'action-button-add-build-output' })
    .click();
  await page.getByLabel('number-field-quantity').fill('1');
  await page
    .getByLabel('text-field-serial_numbers', { exact: true })
    .fill('15');
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Build output created').waitFor();

  const cell = await page.getByRole('cell', { name: '# 15' });
  const row = await getRowFromCell(cell);

  // Open allocation menu for this output
  await clickOnRowMenu(cell);
  await page.getByRole('menuitem', { name: 'Allocate', exact: true }).click();

  // Select a particular tracked item to allocate
  const allocationCell = await page.getByRole('cell', { name: '002.01-PCBA' });
  const allocationRow = await getRowFromCell(allocationCell);
  await clickOnRowMenu(allocationCell);
  await page
    .getByRole('menuitem', { name: 'Allocate Stock', exact: true })
    .click();

  // Check for expected text
  await page
    .getByLabel('Build Output', { exact: true })
    .getByText('Serial Number: 15')
    .waitFor();

  // The stock item should be pre-filled based on serial number
  await page.getByRole('cell', { name: 'Thumbnail 002.01-PCBA |' }).waitFor();
  await page.getByRole('button', { name: 'Submit' }).isEnabled();
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.getByText('Stock items allocated').waitFor();

  await allocationRow.getByText('1 / 1').waitFor();

  // Close the allocation wizard
  await page.getByRole('banner').getByRole('button').click();

  // Check that the output is now allocated as expected
  await row.getByText('1 / 6').waitFor();
  await row.getByText('0 / 2').waitFor();

  // Cancel the build output to return to the original state
  await cancelBuildOutput(cell);

  // Next, complete a new output and auto-allocate items based on serial number
  // Cancel build output "#16" if it exists
  const existingCell16 = await page.getByRole('cell', { name: '# 16' });
  if (await existingCell16.isVisible()) {
    await cancelBuildOutput(existingCell16);
  }

  await page
    .getByRole('button', { name: 'action-button-add-build-output' })
    .click();
  await page.getByLabel('number-field-quantity').fill('1');
  await page
    .getByLabel('text-field-serial_numbers', { exact: true })
    .fill('16');
  await page
    .locator('label')
    .filter({ hasText: 'Auto Allocate Serial' })
    .locator('div')
    .first()
    .click();
  await page.getByRole('button', { name: 'Submit' }).click();

  const newCell = await page.getByRole('cell', { name: '# 16' });
  const newRow = await getRowFromCell(newCell);

  await newRow.getByText('1 / 6').waitFor();
  await newRow.getByText('0 / 2').waitFor();

  // Cancel this output too
  await cancelBuildOutput(newCell);
});

test('Build Order - Filters', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  await navigate(page, 'manufacturing/index/buildorders');

  await clearTableFilters(page);

  // Check for expected pagination text i.e. (1 - 24 / 24)
  // Note: Due to other concurrent tests, the number of build orders may vary
  await page.getByText(/1 - \d+ \/ \d+/).waitFor();
  await page.getByRole('cell', { name: 'BO0023' }).waitFor();

  // Toggle 'Outstanding' filter
  await setTableChoiceFilter(page, 'Outstanding', 'Yes');
  await page.getByRole('cell', { name: 'BO0017' }).waitFor();

  await clearTableFilters(page);
  await setTableChoiceFilter(page, 'Outstanding', 'No');

  await page.getByText('1 - 6 / 6').waitFor();

  await clearTableFilters(page);

  // Filter by custom status code
  await setTableChoiceFilter(page, 'Status', 'Pending Approval');

  // Single result - navigate through to the build order
  await page.getByText('1 - 1 / 1').waitFor();
  await page.getByRole('cell', { name: 'BO0023' }).click();

  await page.getByText('On Hold').first().waitFor();
  await page.getByText('Pending Approval').first().waitFor();
});

test('Build Order - Duplicate', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  await navigate(page, 'manufacturing/build-order/24/details');
  await page.getByLabel('action-menu-build-order-').click();
  await page.getByLabel('action-menu-build-order-actions-duplicate').click();

  // Ensure a new reference is suggested
  await expect(
    page.getByLabel('text-field-reference', { exact: true })
  ).not.toBeEmpty();

  // Submit the duplicate request and ensure it completes
  await page.getByRole('button', { name: 'Submit' }).isEnabled();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByRole('tab', { name: 'Build Details' }).waitFor();
  await page.getByRole('tab', { name: 'Build Details' }).click();

  await page.getByText('Pending').first().waitFor();
});

// Tests for external build orders
test('Build Order - External', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'manufacturing/index/' });
  await loadTab(page, 'Build Orders');

  // Filter to show only external builds
  await clearTableFilters(page);
  await setTableChoiceFilter(page, 'External', 'Yes');
  await page.getByRole('cell', { name: 'BO0026' }).waitFor();
  await page.getByRole('cell', { name: 'BO0025' }).click();
  await page
    .locator('span')
    .filter({ hasText: /^External$/ })
    .waitFor();

  await loadTab(page, 'Allocated Stock');
  await loadTab(page, 'Incomplete Outputs');
  await page
    .getByText('This build order is fulfilled by an external purchase order')
    .waitFor();

  await loadTab(page, 'External Orders');
  await page.getByRole('cell', { name: 'PO0016' }).click();

  await loadTab(page, 'Attachments');
  await loadTab(page, 'Received Stock');
  await loadTab(page, 'Line Items');

  const cell = await page.getByRole('cell', {
    name: '002.01-PCBA',
    exact: true
  });
  await clickOnRowMenu(cell);

  await page.getByRole('menuitem', { name: 'Receive line item' }).waitFor();
  await page.getByRole('menuitem', { name: 'Duplicate' }).waitFor();
  await page.getByRole('menuitem', { name: 'Edit' }).waitFor();
  await page.getByRole('menuitem', { name: 'View Build Order' }).click();

  // Wait for navigation back to build order detail page
  await page.getByText('Build Order: BO0025', { exact: true }).waitFor();

  // Let's look at BO0026 too
  await navigate(page, 'manufacturing/build-order/26/details');
  await loadTab(page, 'External Orders');

  await page.getByRole('cell', { name: 'PO0017' }).waitFor();
  await page.getByRole('cell', { name: 'PO0018' }).waitFor();
});

test('Build Order - BOM Quantity', async ({ browser }) => {
  // Validate required build order quantities (based on BOM values)

  const page = await doCachedLogin(browser, { url: 'part/81/bom' });

  // Expected quantity values for the BOM items
  await page.getByText('15(+50)').waitFor();
  await page.getByText('10(+100)').waitFor();

  await loadTab(page, 'Part Details');

  // Expected "can build" value: 13
  const canBuild = await page
    .getByRole('cell', { name: 'Can Build' })
    .locator('div');
  const row = await getRowFromCell(canBuild);
  await row.getByText('13').waitFor();

  await loadTab(page, 'Build Orders');
  await page.getByRole('cell', { name: 'BO0016' }).click();

  await loadTab(page, 'Required Parts');

  const line = await page
    .getByRole('cell', { name: 'Thumbnail R_10K_0805_1%' })
    .locator('div');
  const row2 = await getRowFromCell(line);
  await row2.getByText('1,175').first().waitFor();
});
