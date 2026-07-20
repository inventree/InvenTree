import { createApi } from './api';
/** Unit tests for form validation, rendering, etc */
import { expect, test } from './baseFixtures';
import { stevenuser } from './defaults';
import {
  clickOnRowMenu,
  deletePart,
  loadTab,
  navigate,
  openDetailAction
} from './helpers';
import { doCachedLogin } from './login';
import { setSettingState } from './settings';

// Test hover form action in related fields
test('Forms - Hover', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    user: stevenuser,
    url: 'purchasing/index/purchaseorders'
  });

  // Patch user settings to ensure we can see "extra model info" on hover
  const api = await createApi({
    username: stevenuser.username,
    password: stevenuser.testcred
  });

  const response = await api.patch('settings/user/SHOW_EXTRA_MODEL_INFO/', {
    data: {
      value: 'true'
    }
  });

  expect(response.status()).toBe(200);

  await page
    .getByRole('button', { name: 'action-button-add-purchase-' })
    .click();
  await page.getByLabel('related-field-supplier').fill('mou');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(250);
  await page.getByText('Mouser Electronics').first().hover();

  // Check for hover info
  await page.getByText('Company[ID: 2]').waitFor();
  await page.getByRole('link', { name: 'View details' }).waitFor();
});

test('Forms - Stock Item Validation', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    user: stevenuser,
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
  await page.getByLabel('tree-field-location').fill('production');
  await page.getByText('Electronics production facility').click();

  // Create the stock item
  await page.getByLabel('number-field-quantity').fill('123');
  await page.getByRole('button', { name: 'Submit' }).click();

  // Edit the resulting stock item
  await openDetailAction(page, 'stock-item', 'edit');

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
    user: stevenuser,
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

test('Forms - Keep form open option', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    user: stevenuser,
    url: 'stock/location/index/sublocations'
  });
  await page.waitForURL('**/stock/location/index/**');

  await page.getByLabel('action-button-add-stock-location').click();

  // Generate unique location name
  const locationName = `New Sublocation ${new Date().getTime()}`;

  await page.getByLabel('text-field-name', { exact: true }).fill(locationName);

  // Check keep form open switch and submit
  await page.getByRole('switch', { name: 'Keep form open' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();

  // Location should be created, form should remain opened
  await page.getByText('Item Created').waitFor();
  await expect(page.getByRole('dialog')).toBeVisible();

  // Create another location and uncheck this option
  await page
    .getByLabel('text-field-name', { exact: true })
    .fill(`Another ${locationName}`);
  await page.getByRole('switch', { name: 'Keep form open' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();

  // Location should be created, and the form (modal) should disappear
  await page.getByText('Item Created').waitFor();
  await expect(page.getByRole('dialog')).toBeHidden();
});

test('Forms - DateTime Field', async ({ browser }) => {
  // The "started_datetime" / "finished_datetime" test-result fields are only
  // shown when the "TEST_STATION_DATA" global setting is enabled
  const api = await createApi({});
  const settingUrl = 'settings/global/TEST_STATION_DATA/';

  const enableResponse = await api.patch(settingUrl, {
    data: { value: 'true' }
  });
  expect(enableResponse.status()).toBe(200);

  const page = await doCachedLogin(browser, {
    user: stevenuser,
    url: 'stock/item/1194/test_results'
  });
  await page.waitForURL('**/web/stock/**');
  await loadTab(page, 'Test Results');

  const cell = page.getByText('395c6d5586e5fb656901d047be27e1f7');
  await clickOnRowMenu(cell);
  await page.getByRole('menuitem', { name: 'Edit' }).click();

  // Set a value via the Mantine DateTimePicker popup - a button which opens a
  // calendar (for the date) plus separate hour/minute/second spinbuttons
  const setDateTime = async (
    fieldLabel: string,
    day: string,
    hour: string,
    minute: string
  ) => {
    const field = page.getByLabel(fieldLabel).first();
    await expect(field).toBeVisible();
    await field.click();
    await page.getByRole('button', { name: day }).first().click();

    const spinbuttons = page.getByRole('spinbutton');
    await spinbuttons.nth(0).fill(hour);
    await spinbuttons.nth(1).fill(minute);
    await spinbuttons.nth(2).fill('00');

    await page.keyboard.press('Escape');
  };

  await setDateTime(
    'date-time-field-started_datetime',
    '10 March 2024',
    '10',
    '30'
  );
  await setDateTime(
    'date-time-field-finished_datetime',
    '11 March 2024',
    '11',
    '45'
  );

  await expect(page.getByLabel('date-time-field-started_datetime')).toHaveText(
    '2024-03-10 10:30:00'
  );
  await expect(page.getByLabel('date-time-field-finished_datetime')).toHaveText(
    '2024-03-11 11:45:00'
  );

  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Test result updated').waitFor();

  // Restore the global setting to its default value
  const disableResponse = await api.patch(settingUrl, {
    data: { value: 'false' }
  });
  expect(disableResponse.status()).toBe(200);
});

// Test the "nested object" field type, via the "Initial Supplier" section
// of the "Create Part" form
test('Forms - Nested Object Field', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    user: stevenuser,
    url: 'part/category/index/parts'
  });
  await page.waitForURL('**/part/category/index/**');

  await page.getByRole('button', { name: 'action-menu-add-parts' }).click();
  await page
    .getByRole('menuitem', { name: 'action-menu-add-parts-create-part' })
    .click();

  // Generate a unique part name
  const partName = `Test Part ${new Date().getTime()}`;
  await page.getByLabel('text-field-name', { exact: true }).fill(partName);

  // The "Initial Supplier" nested-object field should be visible and expanded by default
  await page.getByText('Supplier Information').waitFor();

  const supplierField = page.getByLabel(
    'related-field-initial_supplier.supplier'
  );
  await expect(supplierField).toBeVisible();
  await supplierField.fill('Mouser');
  await page.getByText('Mouser Electronics').first().click();

  const skuValue = `SKU-${new Date().getTime()}`;
  await page
    .getByLabel('text-field-initial_supplier.sku', { exact: true })
    .fill(skuValue);

  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Item Created').waitFor();

  // Confirm the part was created with the expected name
  await page.getByText(partName).first().waitFor();
});

// Regression for #12266: initial stock fields respect PART_CREATE_INITIAL setting
test('Forms - Initial Stock Field', async ({ browser }) => {
  await setSettingState({ setting: 'PART_CREATE_INITIAL', value: true });

  const partName = `Initial Stock Part ${Date.now()}`;
  await deletePart(partName);

  const page = await doCachedLogin(browser, {
    user: stevenuser,
    url: 'part/category/index/parts'
  });
  await page.waitForURL('**/part/category/index/**');

  await page.getByRole('button', { name: 'action-menu-add-parts' }).click();
  await page
    .getByRole('menuitem', { name: 'action-menu-add-parts-create-part' })
    .click();

  await page.getByLabel('text-field-name', { exact: true }).fill(partName);

  await page.getByText('Initial Stock').waitFor();
  const quantityField = page.getByLabel('number-field-initial_stock.quantity');
  await expect(quantityField).toBeVisible();

  await quantityField.fill('25');
  await page.getByLabel('tree-field-initial_stock.location').fill('production');
  await page.getByText('Electronics production facility').click();

  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Item Created').waitFor();

  await page.getByText(partName).first().click();
  await page.getByRole('tab', { name: 'Stock', exact: true }).click();
  await page.getByText('25').first().waitFor();

  await deletePart(partName);
  await setSettingState({ setting: 'PART_CREATE_INITIAL', value: false });
});

test('Forms - Initial Stock hidden when setting disabled', async ({
  browser
}) => {
  await setSettingState({ setting: 'PART_CREATE_INITIAL', value: false });

  const page = await doCachedLogin(browser, {
    user: stevenuser,
    url: 'part/category/index/parts'
  });
  await page.waitForURL('**/part/category/index/**');

  await page.getByRole('button', { name: 'action-menu-add-parts' }).click();
  await page
    .getByRole('menuitem', { name: 'action-menu-add-parts-create-part' })
    .click();

  await page
    .getByLabel('text-field-name', { exact: true })
    .fill('No Initial Stock');

  await expect(page.getByText('Initial Stock')).toBeHidden();
  await expect(
    page.getByLabel('number-field-initial_stock.quantity')
  ).toBeHidden();
});
