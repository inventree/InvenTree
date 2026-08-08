import { expect } from '@playwright/test';
import { test } from '../baseFixtures';
import { navigate } from '../helpers';
import { doCachedLogin } from '../login';

test('Part - Prev/Next navigation buttons', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  // Navigate to part pk=5 with nav context — middle of sequential range so both buttons appear
  const navParams = '_nav_endpoint=%2Fapi%2Fpart%2F&_nav_ordering=pk';
  await navigate(page, `part/5/?${navParams}`);
  await page.waitForLoadState('networkidle');

  const prevBtn = page.getByTestId('inventree-prev-item');
  const nextBtn = page.getByTestId('inventree-next-item');

  // Both buttons should be visible and enabled
  await expect(prevBtn).toBeVisible();
  await expect(nextBtn).toBeVisible();
  await expect(prevBtn).not.toBeDisabled();
  await expect(nextBtn).not.toBeDisabled();

  // Click next — URL should change away from part/5
  await nextBtn.click();
  await page.waitForURL((url) => !url.pathname.includes('/part/5/'));
  await page.waitForLoadState('networkidle');

  // On the next part prev should be enabled
  await expect(page.getByTestId('inventree-prev-item')).not.toBeDisabled();

  // Click prev — URL should change
  const urlBeforeBack = page.url();
  await page.getByTestId('inventree-prev-item').click();
  await page.waitForURL((url) => url.toString() !== urlBeforeBack);
});
