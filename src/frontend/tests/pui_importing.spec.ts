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

  await page
    .locator('label')
    .filter({ hasText: 'Update Existing RecordsIf' })
    .locator('div')
    .first()
    .click();

  await page.getByRole('button', { name: 'Submit' }).click();

  // Submitting without selecting model type, should show error
  await page.getByText('This field is required.').waitFor();
  await page.getByText('Errors exist for one or more').waitFor();

  await page
    .getByRole('textbox', { name: 'choice-field-model_type' })
    .fill('bom');
  await page.getByRole('option', { name: 'BOM Item', exact: true }).click();
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.getByText('Select the parent assembly').waitFor();
  await page.getByText('Select the component part').waitFor();
  await page.getByText('Existing database identifier for the record').waitFor();

  await page
    .getByRole('textbox', { name: 'import-column-map-reference' })
    .click();
  await page.getByRole('option', { name: 'Ignore this field' }).click();

  await page.getByRole('button', { name: 'Accept Column Mapping' }).click();

  // Check for expected ID values
  for (const itemId of ['16', '17', '15', '23']) {
    await page.getByRole('cell', { name: itemId, exact: true });
  }

  // Import all the records
  await page
    .getByRole('row', { name: 'Select all records Row Not' })
    .getByLabel('Select all records')
    .click();
  await page
    .getByRole('button', { name: 'action-button-import-selected' })
    .click();

  await page.getByText('Data has been imported successfully').waitFor();
  await page.getByRole('button', { name: 'Close' }).click();

  // Confirmation of full import success
  await page.getByRole('cell', { name: '3 / 3' }).first().waitFor();

  // Manually delete records
  await page.getByRole('checkbox', { name: 'Select all records' }).click();
  await page
    .getByRole('button', { name: 'action-button-delete-selected' })
    .click();
  await page.getByRole('button', { name: 'Delete', exact: true }).click();
});

test('Importing - BOM', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    username: 'steven',
    password: 'wizardstaff',
    url: 'part/109/bom'
  });

  // Open the BOM importer wizard
  await page.getByRole('button', { name: 'action-menu-add-bom-items' }).click();

  await page
    .getByRole('menuitem', {
      name: 'action-menu-add-bom-items-import-from-file'
    })
    .click();

  // Select BOM file fixture for import
  const fileInput = await page.locator('input[type="file"]');
  await fileInput.setInputFiles('./tests/fixtures/bom_data.csv');
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.getByText('Mapping data columns to database fields').waitFor();
  await page.getByRole('button', { name: 'Accept Column Mapping' }).click();
  await page.waitForTimeout(500);

  await page.getByText('Importing Data').waitFor();
  await page.getByText('0 / 3').waitFor();

  await page.getByText('Screw for fixing wood').first().waitFor();
  await page.getByText('Leg for a chair or a table').first().waitFor();

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
    .getByRole('dialog', { name: 'Importing Data Upload File' })
    .getByLabel('action-button-delete-selected')
    .waitFor();
  await page.waitForTimeout(200);
  await page
    .getByRole('dialog', { name: 'Importing Data Upload File' })
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

  await page.getByText('0 / 1', { exact: true }).waitFor();

  // Submit a row
  await page
    .getByRole('row', { name: 'Select record 1 2 Thumbnail' })
    .getByLabel('row-action-menu-')
    .click();

  await page.getByRole('menuitem', { name: 'Accept' }).click();
  await page.getByText('0 / 1', { exact: true }).waitFor();
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

test('Importing - Natural Keys', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    username: 'steven',
    password: 'wizardstaff',
    url: 'purchasing/purchase-order/15/line-items'
  });

  // Import line item data, but use natural keys as the import fields
  await page
    .getByRole('button', { name: 'action-button-import-line-' })
    .click();

  const fileInput = await page.locator('input[type="file"]');
  await fileInput.setInputFiles('./tests/fixtures/po_data_natural_keys.csv');
  await page.getByRole('button', { name: 'Submit' }).click();

  // Attempt import with missing required fields
  await page.getByRole('button', { name: 'Accept Column Mapping' }).click();
  await page.getByText('Some required fields have not been mapped').waitFor();

  // Select different columns for data import
  // We will use the "SKU" field to map to the supplier part
  await page.getByRole('textbox', { name: 'import-column-map-part' }).click();
  await page.getByRole('option', { name: 'SKU' }).click();

  // Other import fields will be left as default
  await page.getByRole('button', { name: 'Accept Column Mapping' }).click();

  // Check for expected values to be displayed
  await page.getByText('PRO-ZEN').first().waitFor();
  await page.getByText('Project Zenith').first().waitFor();
  await page.getByText('my-custom-reference').first().waitFor();
  await page.getByText('Factory/Mechanical Lab').first().waitFor();
  await page.getByText('FUT-43861-DDU').first().waitFor();
  await page.getByText('FUT-82092-CQB').first().waitFor();
  await page.getByText('2026-01-30').first().waitFor();

  // Let's import all the data
  await page
    .getByRole('row', { name: 'Select all records Row Not' })
    .getByLabel('Select all records')
    .click();
  await page
    .getByRole('button', { name: 'action-button-import-selected' })
    .click();

  await page.getByText('Data has been imported successfully').waitFor();
  await page.getByRole('button', { name: 'Close' }).click();
});
