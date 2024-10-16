import { test } from '../baseFixtures.ts';
import { baseUrl } from '../defaults.ts';
import { doQuickLogin } from '../login.ts';

test('Pages - Build Order', async ({ page }) => {
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

test('Pages - Build Order - Build Outputs', async ({ page }) => {
  await doQuickLogin(page);

  await page.goto(`${baseUrl}/part/`);

  // Navigate to the correct build order
  await page.getByRole('tab', { name: 'Manufacturing', exact: true }).click();

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
    sn = parseInt(placeholder.split(':')[1].trim());
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
  const row = await cell.locator('xpath=ancestor::tr').first();
  await row.getByLabel(/row-action-menu-/i).click();
  await page.getByRole('menuitem', { name: 'Cancel' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Build outputs have been cancelled').waitFor();

  // Complete the other output
  const cell2 = await page.getByRole('cell', { name: `# ${sn + 1}` });
  const row2 = await cell2.locator('xpath=ancestor::tr').first();
  await row2.getByLabel(/row-action-menu-/i).click();
  await page.getByRole('menuitem', { name: 'Complete' }).click();
  await page.getByLabel('related-field-location').click();
  await page.getByText('Mechanical Lab').click();
  await page.waitForTimeout(250);
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Build outputs have been completed').waitFor();
});
