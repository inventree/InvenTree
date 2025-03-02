import { test } from '../baseFixtures.js';
import { navigate } from '../helpers.js';
import { doQuickLogin } from '../login.js';

test('Core User/Group', async ({ page }) => {
  await doQuickLogin(page);

  // groups
  await navigate(page, '/core');
  await page.getByText('System Overview', { exact: true }).click();
  await page.getByRole('tab', { name: 'Groups' }).click();
  await page.getByRole('cell', { name: 'all access' }).click();
  await page.getByText('Group: all access', { exact: true }).click();
  await page.getByLabel('breadcrumb-1-groups').click();

  // users
  await page.getByRole('tab', { name: 'Users' }).click();
  await page.getByRole('cell', { name: 'admin' }).click();
  await page.getByText('User: admin', { exact: true }).waitFor();
  await page.getByLabel('User Details').waitFor();
});
