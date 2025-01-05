import { expect, test } from './baseFixtures.js';
import { apiUrl, baseUrl } from './defaults.js';
import { doQuickLogin } from './login.js';
import { setSettingState } from './settings.js';

/**
 * Adjust language and color settings
 */
test('Settings - Language / Color', async ({ page }) => {
  await doQuickLogin(page);

  await page.getByRole('button', { name: 'Ally Access' }).click();
  await page.getByRole('menuitem', { name: 'Logout' }).click();
  await page.getByRole('button', { name: 'Send me an email' }).click();
  await page.getByRole('button').nth(3).click();
  await page.getByLabel('Select language').first().click();
  await page.getByRole('option', { name: 'German' }).click();
  await page.waitForTimeout(200);

  await page.getByRole('button', { name: 'Benutzername und Passwort' }).click();
  await page.getByPlaceholder('Ihr Benutzername').click();
  await page.getByPlaceholder('Ihr Benutzername').fill('admin');
  await page.getByPlaceholder('Ihr Benutzername').press('Tab');
  await page.getByPlaceholder('Dein Passwort').fill('inventree');
  await page.getByRole('button', { name: 'Anmelden' }).click();
  await page.waitForTimeout(200);

  // Note: changes to the dashboard have invalidated these tests (for now)
  // await page
  //   .locator('span')
  //   .filter({ hasText: 'AnzeigeneinstellungenFarbmodusSprache' })
  //   .getByRole('button')
  //   .click();
  // await page
  //   .locator('span')
  //   .filter({ hasText: 'AnzeigeneinstellungenFarbmodusSprache' })
  //   .getByRole('button')
  //   .click();

  await page.getByRole('tab', { name: 'Dashboard' }).click();
  await page.waitForURL('**/platform/home');
});

test('Settings - Admin', async ({ page }) => {
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
  await page.locator('label').filter({ hasText: 'System Settings' }).click();
  await page.getByText('Base URL', { exact: true }).waitFor();
  await page.getByRole('tab', { name: 'Login' }).click();
  await page.getByRole('tab', { name: 'Barcodes' }).click();
  await page.getByRole('tab', { name: 'Notifications' }).click();
  await page.getByRole('tab', { name: 'Pricing' }).click();
  await page.getByRole('tab', { name: 'Labels' }).click();
  await page.getByRole('tab', { name: 'Reporting' }).click();

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

test('Settings - Admin - Barcode History', async ({ page, request }) => {
  // Login with admin credentials
  await doQuickLogin(page, 'admin', 'inventree');

  // Ensure that the "save scans" setting is enabled
  await setSettingState({
    request: request,
    setting: 'BARCODE_STORE_RESULTS',
    value: true
  });

  // Scan some barcodes (via API calls)
  const barcodes = ['ABC1234', 'XYZ5678', 'QRS9012'];

  barcodes.forEach(async (barcode) => {
    await request.post(`${apiUrl}/barcode/`, {
      data: {
        barcode: barcode
      },
      headers: {
        Authorization: `Basic ${btoa('admin:inventree')}`
      }
    });
  });

  await page.getByRole('button', { name: 'admin' }).click();
  await page.getByRole('menuitem', { name: 'Admin Center' }).click();
  await page.getByRole('tab', { name: 'Barcode Scans' }).click();

  await page.waitForTimeout(500);

  // Barcode history is displayed in table
  barcodes.forEach(async (barcode) => {
    await page.getByText(barcode).first().waitFor();
  });
});

test('Settings - Admin - Unauthorized', async ({ page }) => {
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
