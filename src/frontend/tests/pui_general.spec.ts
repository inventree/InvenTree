import { expect, test } from './baseFixtures.js';
import { adminuser, stevenuser } from './defaults.js';
import { globalSearch } from './helpers.js';
import { doCachedLogin } from './login.js';

/**
 * Test for integration of django admin button
 */
test('General - Admin Button', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    user: adminuser,
    url: 'company/1/details'
  });

  // Click on the admin button
  await page.getByLabel(/action-button-open-in-admin/).click();

  await page.waitForURL('**/test-admin/company/company/1/change/**');
  await page.getByRole('heading', { name: 'Change Company' }).waitFor();
  await page.getByRole('link', { name: 'View on site' }).waitFor();
});

// Tests for the global search functionality
test('General - Search', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    user: stevenuser
  });

  // Open the search drawer with a shortcut
  await page.keyboard.press('Control+/');
  await page.getByRole('textbox', { name: 'global-search-input' }).waitFor();
  await page.keyboard.press('Escape');

  await globalSearch(page, 'another customer');

  // Check for expected results
  await page.locator('a').filter({ hasText: 'Customer B' }).first().waitFor();
  await page.locator('a').filter({ hasText: 'Customer C' }).first().waitFor();
  await page.locator('a').filter({ hasText: 'Customer D' }).first().waitFor();
  await page.locator('a').filter({ hasText: 'Customer E' }).first().waitFor();

  const customerResult = page
    .locator('a')
    .filter({ hasText: 'Customer B' })
    .first();
  await expect(customerResult).toHaveAttribute('href', /\/web\/company\/\d+/);

  const popupPromise = page.context().waitForEvent('page');
  await customerResult.click({ modifiers: ['Control'] });
  const popup = await popupPromise;
  await popup.waitForURL('**/web/company/**');
  await popup.close();

  // Click through to the "Customer" results
  const viewAllCustomers = page.getByRole('link', {
    name: 'view-all-results-customer'
  });
  await expect(viewAllCustomers).toHaveAttribute(
    'href',
    /\/web\/sales\/index\/customers\?search=another\+customer/
  );

  const overviewPopupPromise = page.context().waitForEvent('page');
  await viewAllCustomers.click({ modifiers: ['Control'] });
  const overviewPopup = await overviewPopupPromise;
  await overviewPopup.waitForURL(
    '**/web/sales/index/customers?search=another+customer'
  );
  await overviewPopup.close();

  await viewAllCustomers.click();

  await page.waitForURL('**/sales/index/customers**');
  await page.getByText('Custom table filters are active').waitFor();

  await globalSearch(page, '0402 res');

  await page
    .locator('span')
    .filter({ hasText: 'Parts - 16 results' })
    .first()
    .waitFor();
  await page
    .locator('span')
    .filter({ hasText: 'Supplier Parts - 138 results' })
    .first()
    .waitFor();

  await page
    .getByRole('link', { name: 'view-all-results-manufacturerpart' })
    .click();
  await page.waitForURL('**/purchasing/index/manufacturer-parts**');
  await page.getByRole('cell', { name: 'RT0402BRD07100KL' }).waitFor();
});
