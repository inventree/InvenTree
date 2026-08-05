import { expect, test } from '../baseFixtures.js';
import {
  activateCalendarView,
  clearTableFilters,
  clickOnRowMenu,
  loadTab,
  navigate
} from '../helpers.js';
import { doCachedLogin } from '../login.js';

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
