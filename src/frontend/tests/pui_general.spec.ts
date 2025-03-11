import { test } from './baseFixtures.js';
import { globalSearch, navigate } from './helpers.js';
import { doQuickLogin } from './login.js';

/**
 * Test for integration of django admin button
 */
test('Admin Button', async ({ page }) => {
  await doQuickLogin(page, 'admin', 'inventree');
  await navigate(page, 'company/1/details');

  // Click on the admin button
  await page.getByLabel(/action-button-open-in-admin/).click();

  await page.waitForURL('**/test-admin/company/company/1/change/**');
  await page.getByRole('heading', { name: 'Change Company' }).waitFor();
  await page.getByRole('link', { name: 'View on site' }).waitFor();
});

// Tests for the global search functionality
test('Search', async ({ page }) => {
  await doQuickLogin(page, 'steven', 'wizardstaff');

  await globalSearch(page, 'another customer');

  // Check for expected results
  await page.locator('a').filter({ hasText: 'Customer B' }).first().waitFor();
  await page.locator('a').filter({ hasText: 'Customer C' }).first().waitFor();
  await page.locator('a').filter({ hasText: 'Customer D' }).first().waitFor();
  await page.locator('a').filter({ hasText: 'Customer E' }).first().waitFor();

  // Click through to the "Customer" results
  await page.getByRole('button', { name: 'view-all-results-customer' }).click();

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

  await page.getByLabel('view-all-results-manufacturerpart').click();
  await page.waitForURL('**/purchasing/index/manufacturer-parts**');
  await page.getByRole('cell', { name: 'RT0402BRD07100KL' }).waitFor();
});
