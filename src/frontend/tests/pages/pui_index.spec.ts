import { test } from '../baseFixtures.js';
import { doQuickLogin } from '../login.js';

test('Pages - Index - Dashboard', async ({ page }) => {
  await doQuickLogin(page);

  // Dashboard auto update
  await page.getByRole('tab', { name: 'Dashboard' }).click();
  await page.getByText('Autoupdate').click();
  await page.waitForTimeout(500);
  await page.getByText('Autoupdate').click();
  await page.getByText('This page is a replacement').waitFor();
});
