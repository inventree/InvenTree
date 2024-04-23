import { expect, test } from '@playwright/test';

import { classicUrl, user } from './defaults';

test('CUI - Index', async ({ page }) => {
  await page.goto(`${classicUrl}/api/`);
  await page.goto(`${classicUrl}/index/`, { timeout: 10000 });
  console.log('Page title:', await page.title());
  await expect(page).toHaveTitle(RegExp('^InvenTree.*Sign In$'));
  await expect(page.getByRole('heading', { name: 'Sign In' })).toBeVisible();

  await page.getByLabel('username').fill(user.username);
  await page.getByLabel('password').fill(user.password);
  await page.click('button', { text: 'Sign In' });
  await page.waitForURL('**/index/');

  await page.waitForLoadState('networkidle');
  await expect(page).toHaveTitle('InvenTree Demo Server | Index');
  await expect(page.getByRole('button', { name: user.username })).toBeVisible();
  await expect(
    page.getByRole('link', { name: 'Parts', exact: true })
  ).toBeVisible();
  await expect(
    page.getByRole('link', { name: 'Stock', exact: true })
  ).toBeVisible();
  await expect(
    page.getByRole('link', { name: 'Build', exact: true })
  ).toBeVisible();
  await expect(page.getByRole('button', { name: 'Buy' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Sell' })).toBeVisible();
});
