import { expect, test } from './baseFixtures.js';
import { allaccessuser } from './defaults.js';
import { navigate } from './helpers.js';
import { doLogin } from './login.js';

/**
 * Tests for previous / next navigation on detail pages.
 *
 * NOTE: written against the source tree without a running stack; the exact
 * list URL and row selectors below may need a small adjustment once verified
 * against the test database in CI. See TODO markers.
 */
test('Detail - previous/next navigation from a list', async ({ page }) => {
  await doLogin(page, { user: allaccessuser });

  // Open the parts list (canonical overview URL for the "part" model)
  await navigate(page, 'part/category/index/parts');
  await page.waitForLoadState('networkidle');
  await page.waitForURL(/\/web\/part/);

  // Click the first data row's first cell to open its detail view
  await page.locator('table tbody tr').first().locator('td').first().click();
  await page.waitForURL(/\/web\/part\/\d+/);

  // Navigation buttons should be rendered
  const prevButton = page.getByLabel('previous-object');
  const nextButton = page.getByLabel('next-object');
  await expect(prevButton).toBeVisible();
  await expect(nextButton).toBeVisible();

  // The first row in the list has no "previous"
  await expect(prevButton).toBeDisabled();

  // Clicking "next" moves to a different object
  const beforeUrl = page.url();
  await nextButton.click();
  await page.waitForURL(/\/web\/part\/\d+/);
  await expect(page).not.toHaveURL(beforeUrl);

  // After moving forward, "previous" becomes enabled
  await expect(page.getByLabel('previous-object')).toBeEnabled();
});

test('Detail - no navigation when opened directly', async ({ page }) => {
  await doLogin(page, { user: allaccessuser });

  // Open a detail view directly (no list context)
  await navigate(page, 'part/1/');
  await page.waitForLoadState('networkidle');
  await page.waitForURL(/\/web\/part\/1/);

  // Without a list context, the navigation buttons should be absent
  await expect(page.getByLabel('previous-object')).toHaveCount(0);
  await expect(page.getByLabel('next-object')).toHaveCount(0);
});
