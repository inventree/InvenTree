/** Unit tests for form validation, rendering, etc */
import test from 'playwright/test';
import { navigate } from './helpers';
import { doCachedLogin } from './login';

test('Forms - Stock Item Validation', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    username: 'steven',
    password: 'wizardstaff',
    url: 'stock/location/index/stock-items'
  });

  await page.waitForURL('**/web/stock/location/**');

  // Create new stock item form
  await page.getByLabel('action-button-add-stock-item').click();
  await page.getByRole('button', { name: 'Submit' }).click();

  // Check for validation errors
  await page.getByText('Form Error').waitFor();
  await page.getByText('Errors exist for one or more form fields').waitFor();
  await page.getByText('Valid part must be supplied').waitFor();

  // Adjust other field - the errors should persist
  await page.getByLabel('text-field-batch', { exact: true }).fill('BATCH-123');
  await page.waitForTimeout(250);

  await page.getByText('Valid part must be supplied').waitFor();

  // Fill out fields
  await page.getByLabel('number-field-quantity').fill('-1');
  await page.getByLabel('related-field-part').click();
  await page.getByRole('option', { name: /1551AGY/ }).click();
  await page.getByRole('button', { name: 'Submit' }).click();

  // Check for validation errors
  await page.getByText('Errors exist for one or more form fields').waitFor();
  await page
    .getByText(/Ensure this value is greater than or equal to 0/)
    .first()
    .waitFor();

  // Set location
  await page.getByLabel('related-field-location').click();
  await page.getByText('Electronics production facility').click();

  // Create the stock item
  await page.getByLabel('number-field-quantity').fill('123');
  await page.getByRole('button', { name: 'Submit' }).click();

  // Edit the resulting stock item
  await page.getByLabel('action-menu-stock-item-actions').click();
  await page.getByLabel('action-menu-stock-item-actions-edit').click();

  await page.getByLabel('number-field-purchase_price').fill('-1');

  await page.getByRole('button', { name: 'Submit' }).click();

  await page.getByText('Errors exist for one or more form fields').waitFor();
  await page
    .getByText('Ensure this value is greater than or equal to 0')
    .waitFor();

  // Check the error message still persists after editing a different field
  await page.getByLabel('text-field-packaging', { exact: true }).fill('a box');
  await page.waitForTimeout(250);
  await page
    .getByText('Ensure this value is greater than or equal to 0')
    .waitFor();

  // Correct the price
  await page.getByLabel('number-field-purchase_price').fill('1.2345');
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Item Updated').waitFor();

  // Ensure the stock item has been updated correctly
  await page.getByText('$151.8435').waitFor();
  await page.getByText('$151.8435').waitFor();
  await page.getByText('a box').waitFor();
  await page.getByRole('cell', { name: 'Electronics Lab' }).waitFor();
});

test('Forms - Supplier Validation', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    username: 'steven',
    password: 'wizardstaff',
    url: 'purchasing/index/suppliers'
  });
  await page.waitForURL('**/purchasing/index/**');

  await page.getByLabel('action-button-add-company').click();
  await page
    .getByLabel('text-field-website', { exact: true })
    .fill('not-a-website');

  await page.getByRole('button', { name: 'Submit' }).click();

  // Check for validation errors
  await page.getByText('Form Error').waitFor();
  await page.getByText('Errors exist for one or more').waitFor();
  await page.getByText('This field is required').waitFor();
  await page.getByText('Enter a valid URL.').waitFor();

  // Fill out another field, expect that the errors persist
  await page
    .getByLabel('text-field-description', { exact: true })
    .fill('A description');
  await page.waitForTimeout(250);
  await page.getByText('This field is required').waitFor();
  await page.getByText('Enter a valid URL.').waitFor();

  // Generate a unique supplier name
  const supplierName = `Supplier ${new Date().getTime()}`;

  // Fill with good data
  await page
    .getByLabel('text-field-website', { exact: true })
    .fill('https://www.test-website.co.uk');
  await page.getByLabel('text-field-name', { exact: true }).fill(supplierName);
  await page.getByRole('button', { name: 'Submit' }).click();

  await page.getByText('A description').first().waitFor();
  await page
    .getByRole('link', { name: 'https://www.test-website.co.uk' })
    .waitFor();

  // Now, try to create another new supplier with the same name
  await navigate(page, 'purchasing/index/suppliers');
  await page.waitForURL('**/purchasing/index/**');
  await page.getByLabel('action-button-add-company').click();
  await page.getByLabel('text-field-name', { exact: true }).fill(supplierName);
  await page.getByRole('button', { name: 'Submit' }).click();

  // Is prevented, due to uniqueness requirements
  await page.getByText('Form Error').waitFor();
  await page.getByRole('button', { name: 'Cancel' }).click();
});
