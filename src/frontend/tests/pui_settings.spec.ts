import { expect, test } from './baseFixtures.js';
import { baseUrl } from './defaults.js';
import { doQuickLogin } from './login.js';

test('PUI - Admin', async ({ page }) => {
  // Note here we login with admin access
  await doQuickLogin(page, 'admin', 'inventree');

  // User settings
  await page.getByRole('button', { name: 'admin' }).click();
  await page.getByRole('menuitem', { name: 'Account settings' }).click();
  await page.getByRole('tab', { name: 'Security' }).click();

  await page.getByRole('tab', { name: 'Display Options' }).click();
  await page.getByText('Date Format').waitFor();
  await page.getByRole('tab', { name: 'Search' }).click();
  await page.getByText('Regex Search').waitFor();
  await page.getByRole('tab', { name: 'Notifications' }).click();
  await page.getByRole('tab', { name: 'Reporting' }).click();
  await page.getByText('Inline report display').waitFor();

  // System Settings
  await page.getByRole('link', { name: 'Switch to System Setting' }).click();
  await page.getByText('Base URL', { exact: true }).waitFor();
  await page.getByRole('tab', { name: 'Login' }).click();
  await page.getByRole('tab', { name: 'Barcodes' }).click();
  await page.getByRole('tab', { name: 'Notifications' }).click();
  await page.getByRole('tab', { name: 'Pricing' }).click();
  await page.getByRole('tab', { name: 'Labels' }).click();
  await page.getByRole('tab', { name: 'Reporting' }).click();

  await page.getByRole('tab', { name: 'Stocktake' }).click();
  await page.getByRole('tab', { name: 'Build Orders' }).click();
  await page.getByRole('tab', { name: 'Purchase Orders' }).click();
  await page.getByRole('tab', { name: 'Sales Orders' }).click();
  await page.getByRole('tab', { name: 'Return Orders' }).click();

  // Admin Center
  await page.getByRole('button', { name: 'admin' }).click();
  await page.getByRole('menuitem', { name: 'Admin Center' }).click();
  await page.getByRole('tab', { name: 'Background Tasks' }).click();
  await page.getByRole('tab', { name: 'Error Reports' }).click();
  await page.getByRole('tab', { name: 'Currencies' }).click();
  await page.getByRole('tab', { name: 'Project Codes' }).click();
  await page.getByRole('tab', { name: 'Custom Units' }).click();
  await page.getByRole('tab', { name: 'Part Parameters' }).click();
  await page.getByRole('tab', { name: 'Category Parameters' }).click();
  await page.getByRole('tab', { name: 'Label Templates' }).click();
  await page.getByRole('tab', { name: 'Report Templates' }).click();
  await page.getByRole('tab', { name: 'Plugins' }).click();

  // Adjust some "location type" items
  await page.getByRole('tab', { name: 'Location Types' }).click();

  // Edit first item
  await page.getByLabel('row-action-menu-0').click();
  await page.getByRole('menuitem', { name: 'Edit' }).click();
  await expect(page.getByLabel('text-field-name')).toHaveValue('Room');
  await expect(page.getByLabel('text-field-description')).toHaveValue('A room');
  await page.getByLabel('text-field-name').fill('Large Room');
  await page.waitForTimeout(500);
  await page.getByLabel('text-field-description').fill('A large room');
  await page.waitForTimeout(500);
  await page.getByRole('button', { name: 'Submit' }).click();

  // Edit second item
  await page.getByLabel('row-action-menu-1').click();
  await page.getByRole('menuitem', { name: 'Edit' }).click();
  await expect(page.getByLabel('text-field-name')).toHaveValue('Box (Large)');
  await expect(page.getByLabel('text-field-description')).toHaveValue(
    'Large cardboard box'
  );
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Edit first item again (revert values)
  await page.getByLabel('row-action-menu-0').click();
  await page.getByRole('menuitem', { name: 'Edit' }).click();
  await expect(page.getByLabel('text-field-name')).toHaveValue('Large Room');
  await expect(page.getByLabel('text-field-description')).toHaveValue(
    'A large room'
  );
  await page.getByLabel('text-field-name').fill('Room');
  await page.waitForTimeout(500);
  await page.getByLabel('text-field-description').fill('A room');
  await page.waitForTimeout(500);
  await page.getByRole('button', { name: 'Submit' }).click();
});

test('PUI - Admin - Unauthorized', async ({ page }) => {
  // Try to access "admin" page with a non-staff user
  await doQuickLogin(page, 'allaccess', 'nolimits');

  await page.goto(`${baseUrl}/settings/admin/`);
  await page.waitForURL('**/settings/admin/**');

  // Should get a permission denied message
  await page.getByText('Permission Denied').waitFor();
  await page
    .getByRole('button', { name: 'Return to the index page' })
    .waitFor();

  // Try to access user settings page (should be accessible)
  await page.goto(`${baseUrl}/settings/user/`);
  await page.waitForURL('**/settings/user/**');

  await page.getByRole('tab', { name: 'Display Options' }).click();
  await page.getByRole('tab', { name: 'Account' }).click();

  // Try to access global settings page
  await page.goto(`${baseUrl}/settings/system/`);
  await page.waitForURL('**/settings/system/**');

  await page.getByText('Permission Denied').waitFor();
  await page
    .getByRole('button', { name: 'Return to the index page' })
    .waitFor();
});
