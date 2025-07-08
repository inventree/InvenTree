import test from '@playwright/test';
import { doCachedLogin } from './login';

test('Importing - Admin Center', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    username: 'steven',
    password: 'wizardstaff',
    url: 'settings/admin/import'
  });

  await page
    .getByRole('button', { name: 'action-button-create-import-' })
    .click();

  const fileInput = await page.locator('input[type="file"]');
  await fileInput.setInputFiles('./tests/fixtures/bom_data.csv');
  await page.getByRole('button', { name: 'Submit' }).click();

  // Submitting without selecting model type, should show error
  await page.getByText('This field is required.').waitFor();
  await page.getByText('Errors exist for one or more').waitFor();

  await page
    .getByRole('textbox', { name: 'choice-field-model_type' })
    .fill('Cat');
  await page
    .getByRole('option', { name: 'Part Category', exact: true })
    .click();
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.getByText('Description (optional)').waitFor();
  await page.getByText('Parent Category').waitFor();
});

test('Importing - BOM', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    username: 'steven',
    password: 'wizardstaff',
    url: 'part/87/bom'
  });

  await page
    .getByRole('button', { name: 'action-button-import-bom-data' })
    .click();

  // Select BOM file fixture for import
  const fileInput = await page.locator('input[type="file"]');
  await fileInput.setInputFiles('./tests/fixtures/bom_data.csv');
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.getByText('Mapping data columns to database fields').waitFor();
  await page.getByRole('button', { name: 'Accept Column Mapping' }).click();
  await page.waitForTimeout(500);

  await page.getByText('Importing Data').waitFor();
  await page.getByText('0 / 4').waitFor();

  await page.getByText('Torx head screw, M3 thread, 10.0mm').first().waitFor();
  await page.getByText('Small plastic enclosure, black').first().waitFor();

  // Select some rows
  await page
    .getByRole('row', { name: 'Select record 1 0 Thumbnail' })
    .getByLabel('Select record')
    .click();
  await page
    .getByRole('row', { name: 'Select record 2 1 Thumbnail' })
    .getByLabel('Select record')
    .click();

  // Delete selected rows
  await page
    .getByRole('dialog', { name: 'Importing Data Upload File 2' })
    .getByLabel('action-button-delete-selected')
    .click();
  await page.getByRole('button', { name: 'Delete', exact: true }).click();

  await page.getByText('Success', { exact: true }).waitFor();
  await page.getByText('Items deleted', { exact: true }).waitFor();

  // Edit a row
  await page
    .getByRole('row', { name: 'Select record 1 2 Thumbnail' })
    .getByLabel('row-action-menu-')
    .click();
  await page.getByRole('menuitem', { name: 'Edit' }).click();
  await page.getByRole('textbox', { name: 'number-field-quantity' }).fill('12');

  await page.waitForTimeout(250);
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.waitForTimeout(250);

  await page.getByText('0 / 2', { exact: true }).waitFor();

  // Submit a row
  await page
    .getByRole('row', { name: 'Select record 1 2 Thumbnail' })
    .getByLabel('row-action-menu-')
    .click();
  await page.getByRole('menuitem', { name: 'Accept' }).click();
  await page.getByText('1 / 2', { exact: true }).waitFor();
});

test('Importing - Purchase Order', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    username: 'steven',
    password: 'wizardstaff',
    url: 'purchasing/purchase-order/15/line-items'
  });

  await page
    .getByRole('button', { name: 'action-button-import-line-' })
    .click();

  const fileInput = await page.locator('input[type="file"]');
  await fileInput.setInputFiles('./tests/fixtures/po_data.csv');
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.getByRole('cell', { name: 'Database Field' }).waitFor();
  await page.getByRole('cell', { name: 'Field Description' }).waitFor();
});
