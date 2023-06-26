import { test, expect } from '@playwright/test';

test('check test output', async ({ page }) => {
  await page.goto('./api/');
  await page.goto('./platform/');

  //await expect(page).toHaveTitle(/Welcome to the new frontend!/);
});
