import { expect, test } from './baseFixtures.js';
import { adminuser, apiUrl, stevenuser } from './defaults.js';
import { globalSearch, openInNewTab } from './helpers.js';
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

  const popup = await openInNewTab(page, customerResult, '**/web/company/**');
  await popup.close();

  // Click through to the "Customer" results
  const viewAllCustomers = page.getByRole('link', {
    name: 'view-all-results-customer'
  });
  await expect(viewAllCustomers).toHaveAttribute(
    'href',
    /\/web\/sales\/index\/customers\?search=another\+customer/
  );

  const overviewPopup = await openInNewTab(
    page,
    viewAllCustomers,
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

/**
 * Test that the API documentation page actually renders.
 *
 * The /api-doc/ view is a thin HTML shell which loads Redoc from a CDN;
 * a 200 response does not mean that the documentation is displayed.
 * Ref: https://github.com/inventree/InvenTree/issues/13200
 */
test('General - API Documentation', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    user: stevenuser
  });

  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));

  // Note: api-doc page is not forwarded to port 5173
  const docUrl = new URL('http://localhost:8000/api-doc/', apiUrl).toString();
  const response = await page.goto(docUrl);
  await page.waitForLoadState('networkidle');
  expect(response?.status()).toBe(200);

  // Redoc renders the schema title and the generated API endpoints
  await page
    .getByRole('heading', { name: /InvenTree API/ })
    .first()
    .waitFor({ timeout: 30000 });

  await page.getByText('Download OpenAPI specification').first().waitFor();
  await page.getByText('/api/part/', { exact: false }).first().waitFor();

  expect(errors).toEqual([]);
});
