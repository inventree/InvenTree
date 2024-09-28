/** Unit tests for form validation, rendering, etc */
import test from 'playwright/test';

import { baseUrl } from './defaults';
import { doQuickLogin } from './login';

test('Forms - Stock Item Validation', async ({ page }) => {
  await doQuickLogin(page, 'steven', 'wizardstaff');
  await page.goto(`${baseUrl}/stock/location/index/stock-items`);
  await page.waitForURL('**/platform/stock/location/**');

  // Create new stock item form
  await page.getByLabel('action-button-add-stock-item').click();
  await page.getByRole('button', { name: 'Submit' }).click();

  // Check for validation errors
  await page.getByText('Form Error').waitFor();
  await page.getByText('Errors exist for one or more form fields').waitFor();
  await page.getByText('Valid part must be supplied').waitFor();

  // Adjust other field - the errors should persist
  await page.getByLabel('text-field-batch').fill('BATCH-123');
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
  await page.getByLabel('text-field-packaging').fill('a box');
  await page.waitForTimeout(250);
  await page
    .getByText('Ensure this value is greater than or equal to 0')
    .waitFor();

  // Correct the price
  await page.getByLabel('number-field-purchase_price').fill('1.2345');
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Item Updated').waitFor();

  await page.waitForTimeout(1000);
});
