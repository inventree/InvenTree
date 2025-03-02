import { test } from '../baseFixtures.js';
import { loadTab, navigate } from '../helpers.js';
import { doQuickLogin } from '../login.js';

test('Core User/Group/Contact', async ({ page }) => {
  await doQuickLogin(page);

  // groups
  await navigate(page, '/core');
  await page.getByText('System Overview', { exact: true }).click();
  await loadTab(page, 'Groups');
  await page.getByRole('cell', { name: 'all access' }).click();
  await page.getByText('Group: all access', { exact: true }).click();
  await page.getByLabel('breadcrumb-1-groups').click();

  // users
  await loadTab(page, 'Users');
  await page.getByRole('cell', { name: 'admin' }).click();
  await page.getByText('User: admin', { exact: true }).waitFor();
  await page.getByLabel('User Details').waitFor();
  await page.getByLabel('breadcrumb-1-users').click();

  // contacts
  await loadTab(page, 'Contacts');
  await page.getByRole('cell', { name: 'Adrian Briggs' }).waitFor();
});
