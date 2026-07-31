import { expect } from '@playwright/test';
import { test } from '../baseFixtures';
import { navigate } from '../helpers';
import { doCachedLogin } from '../login';

test('Part - Prev/Next navigation buttons', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  // Navigate to a part detail page that is known to have siblings (pk=1)
  await navigate(page, 'part/1/');
  await page.waitForLoadState('networkidle');

  const prevBtn = page.getByTestId('inventree-prev-item');
  const nextBtn = page.getByTestId('inventree-next-item');

  await expect(prevBtn).toBeVisible();
  await expect(nextBtn).toBeVisible();

  // pk=1 is the first part, so prev should be disabled
  await expect(prevBtn).toBeDisabled();

  // Next should be enabled and navigate forward
  await expect(nextBtn).not.toBeDisabled();
  const currentUrl = page.url();
  await nextBtn.click();
  await page.waitForURL((url) => url.toString() !== currentUrl);
  await page.waitForLoadState('networkidle');

  // Now on the next part - prev should be enabled
  const prevBtnNext = page.getByTestId('inventree-prev-item');
  await expect(prevBtnNext).not.toBeDisabled();

  // Navigate back
  await prevBtnNext.click();
  await page.waitForURL('**/part/1/**');
});
