import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {
  await page.goto('./platform/');
  await page.getByPlaceholder('Benutzername').click();
  await page.getByPlaceholder('Benutzername').fill('admin');
  await page.getByPlaceholder('Benutzername').press('Tab');
  await page.getByPlaceholder('Passwort').fill('inventree');
  await page.getByRole('button', { name: 'Einloggen' }).click();
  await page
    .locator('div')
    .filter({ hasText: /^No selection$/ })
    .getByRole('button')
    .click();
  await page.getByPlaceholder('hello@mantine.dev').fill('admin');
  await page.getByPlaceholder('hello@mantine.dev').press('Tab');
  await page.getByPlaceholder('Your password').fill('inventree');
  await page.getByRole('button', { name: 'Login' }).click();

  await page.getByRole('button').nth(2).click();

  await page
    .getByText(
      'Localhost|InvenTree Demo Servermati mairiHomePartDashboardAutoupdateSubscribed P'
    )
    .click();
  await page.getByRole('tab', { name: 'Home' }).click();
  await page.getByText('Home').nth(1).isVisible();
  await page.getByRole('tab', { name: 'Part' }).click();
  await page.getByText('Part').nth(1).isVisible();
  await page.locator('[id="mantine-h82hs7qzx-tab-\\/"]').click();
  await page.getByText('Dashboard').isVisible();
  await page.getByRole('button', { name: 'mati mairi' }).click();
  await page.getByRole('menuitem', { name: 'Profile' }).click();
  await page.getByRole('heading', { name: 'Error' }).isVisible();
});
