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

  await page.getByText('Processing Data').waitFor();
  await page.getByText('0 / 4').waitFor();
  await page
    .getByLabel('Importing DataUpload FileMap')
    .getByText('002.01-PCBA | Widget Board')
    .waitFor();
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
