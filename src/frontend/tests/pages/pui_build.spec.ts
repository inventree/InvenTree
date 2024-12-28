import { test } from '../baseFixtures.ts';
import { baseUrl } from '../defaults.ts';
import {
  clearTableFilters,
  getRowFromCell,
  setTableChoiceFilter
} from '../helpers.ts';
import { doQuickLogin } from '../login.ts';

test('Build Order - Basic Tests', async ({ page }) => {
  await doQuickLogin(page);

  await page.goto(`${baseUrl}/part/`);

  // Navigate to the correct build order
  await page.getByRole('tab', { name: 'Manufacturing', exact: true }).click();

  // We have now loaded the "Build Order" table. Check for some expected texts
  await page.getByText('On Hold').first().waitFor();
  await page.getByText('Pending').first().waitFor();

  // Load a particular build order
  await page.getByRole('cell', { name: 'BO0017' }).click();

  // This build order should be "on hold"
  await page.getByText('On Hold').first().waitFor();

  // Edit the build order (via keyboard shortcut)
  await page.keyboard.press('Control+E');
  await page.getByLabel('text-field-title').waitFor();
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
  await page.getByRole('tab', { name: 'Attachments' }).click();
  await page.getByRole('tab', { name: 'Notes' }).click();
  await page.getByRole('tab', { name: 'Incomplete Outputs' }).click();
  await page.getByRole('tab', { name: 'Line Items' }).click();
  await page.getByRole('tab', { name: 'Allocated Stock' }).click();

  // Check for expected text in the table
  await page.getByText('R_10R_0402_1%').waitFor();
  await page
    .getByRole('cell', { name: 'R38, R39, R40, R41, R42, R43' })
    .waitFor();

  // Check "test results"
  await page.getByRole('tab', { name: 'Test Results' }).click();
  await page.getByText('Quantity: 25').waitFor();
  await page.getByText('Continuity Checks').waitFor();
  await page
    .getByRole('row', { name: 'Quantity: 16 No location set' })
    .getByRole('button')
    .hover();
  await page.getByText('Add Test Result').waitFor();

  // Click through to the "parent" build
  await page.getByRole('tab', { name: 'Build Details' }).click();
  await page.getByRole('link', { name: 'BO0010' }).click();
  await page
    .getByLabel('Build Details')
    .getByText('Making a high level assembly')
    .waitFor();
});

test('Build Order - Build Outputs', async ({ page }) => {
  await doQuickLogin(page);

  await page.goto(`${baseUrl}/manufacturing/index/`);
  await page.getByRole('tab', { name: 'Build Orders', exact: true }).click();

  // We have now loaded the "Build Order" table. Check for some expected texts
  await page.getByText('On Hold').first().waitFor();
  await page.getByText('Pending').first().waitFor();

  await page.getByRole('cell', { name: 'BO0011' }).click();
  await page.getByRole('tab', { name: 'Incomplete Outputs' }).click();

  // Create a new build output
  await page.getByLabel('action-button-add-build-output').click();
  await page.getByLabel('number-field-quantity').fill('5');

  const placeholder = await page
    .getByLabel('text-field-serial_numbers')
    .getAttribute('placeholder');

  let sn = 1;

  if (!!placeholder && placeholder.includes('Next serial number')) {
    sn = Number.parseInt(placeholder.split(':')[1].trim());
  }

  // Generate some new serial numbers
  await page.getByLabel('text-field-serial_numbers').fill(`${sn}, ${sn + 1}`);

  await page.getByLabel('text-field-batch_code').fill('BATCH12345');
  await page.getByLabel('related-field-location').click();
  await page.getByText('Reel Storage').click();
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
});

test('Build Order - Allocation', async ({ page }) => {
  await doQuickLogin(page);

  await page.goto(`${baseUrl}/manufacturing/build-order/1/line-items`);

  // Expand the R_10K_0805 line item
  await page.getByText('R_10K_0805_1%').first().click();
  await page.getByText('Reel Storage').waitFor();
  await page.getByText('R_10K_0805_1%').first().click();

  // The capacitor stock should be fully allocated
  const cell = await page.getByRole('cell', { name: /C_1uF_0805/ });
  const row = await getRowFromCell(cell);

  await row.getByText(/150 \/ 150/).waitFor();

  // Expand this row
  await cell.click();
  await page.getByRole('cell', { name: '2022-4-27', exact: true }).waitFor();
  await page.getByRole('cell', { name: 'Reel Storage', exact: true }).waitFor();

  // Navigate to the "Incomplete Outputs" tab
  await page.getByRole('tab', { name: 'Incomplete Outputs' }).click();

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
      available: '39',
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
  const redRow = await redWidget.locator('xpath=ancestor::tr').first();

  await redRow.getByLabel(/row-action-menu-/i).click();
  await page
    .getByRole('menuitem', { name: 'Allocate Stock', exact: true })
    .waitFor();
  await page
    .getByRole('menuitem', { name: 'Deallocate Stock', exact: true })
    .waitFor();
});

test('Build Order - Filters', async ({ page }) => {
  await doQuickLogin(page);

  await page.goto(`${baseUrl}/manufacturing/index/buildorders`);

  await clearTableFilters(page);
  await page.getByText('1 - 24 / 24').waitFor();

  // Toggle 'Outstanding' filter
  await setTableChoiceFilter(page, 'Outstanding', 'Yes');
  await page.getByText('1 - 18 / 18').waitFor();
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
