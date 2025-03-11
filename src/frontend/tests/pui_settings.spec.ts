import { expect, test } from './baseFixtures.js';
import { apiUrl } from './defaults.js';
import { getRowFromCell, loadTab, navigate } from './helpers.js';
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
  await page.getByLabel('Language toggle').click();
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
  await loadTab(page, 'Security');

  await loadTab(page, 'Display Options');
  await page.getByText('Date Format').waitFor();
  await loadTab(page, 'Search');
  await page.getByText('Regex Search').waitFor();
  await loadTab(page, 'Notifications');
  await loadTab(page, 'Reporting');
  await page.getByText('Inline report display').waitFor();

  // System Settings
  await page.locator('label').filter({ hasText: 'System Settings' }).click();
  await page.getByText('Base URL', { exact: true }).waitFor();
  await loadTab(page, 'Login');
  await loadTab(page, 'Barcodes');
  await loadTab(page, 'Notifications');
  await loadTab(page, 'Pricing');
  await loadTab(page, 'Labels');
  await loadTab(page, 'Reporting');

  await loadTab(page, 'Build Orders');
  await loadTab(page, 'Purchase Orders');
  await loadTab(page, 'Sales Orders');
  await loadTab(page, 'Return Orders');

  // Admin Center
  await page.getByRole('button', { name: 'admin' }).click();
  await page.getByRole('menuitem', { name: 'Admin Center' }).click();
  await loadTab(page, 'Background Tasks');
  await loadTab(page, 'Error Reports');
  await loadTab(page, 'Currencies');
  await loadTab(page, 'Project Codes');
  await loadTab(page, 'Custom Units');
  await loadTab(page, 'Part Parameters');
  await loadTab(page, 'Category Parameters');
  await loadTab(page, 'Label Templates');
  await loadTab(page, 'Report Templates');
  await loadTab(page, 'Plugins');

  // Adjust some "location type" items
  await loadTab(page, 'Location Types');

  // Edit first item ('Room')
  const roomCell = await page.getByRole('cell', { name: 'Room', exact: true });
  const roomRow = await getRowFromCell(roomCell);

  await roomRow.getByLabel(/row-action-menu-/i).click();

  await page.getByRole('menuitem', { name: 'Edit' }).click();
  await expect(page.getByLabel('text-field-name')).toHaveValue('Room');

  // Toggle the "description" field
  const oldDescription = await page
    .getByLabel('text-field-description')
    .inputValue();

  const newDescription = `${oldDescription} (edited)`;

  await page.getByLabel('text-field-description').fill(newDescription);
  await page.waitForTimeout(500);
  await page.getByRole('button', { name: 'Submit' }).click();

  // Edit second item - 'Box (Large)'
  const boxCell = await page.getByRole('cell', {
    name: 'Box (Large)',
    exact: true
  });
  const boxRow = await getRowFromCell(boxCell);

  await boxRow.getByLabel(/row-action-menu-/i).click();

  await page.getByRole('menuitem', { name: 'Edit' }).click();
  await expect(page.getByLabel('text-field-name')).toHaveValue('Box (Large)');
  await expect(page.getByLabel('text-field-description')).toHaveValue(
    'Large cardboard box'
  );
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Edit first item again (revert values)
  await roomRow.getByLabel(/row-action-menu-/i).click();
  await page.getByRole('menuitem', { name: 'Edit' }).click();
  await page.getByLabel('text-field-name').fill('Room');
  await page.waitForTimeout(500);
  await page
    .getByLabel('text-field-description')
    .fill(newDescription.replaceAll(' (edited)', ''));
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
  await loadTab(page, 'Barcode Scans');

  await page.waitForTimeout(500);

  // Barcode history is displayed in table
  barcodes.forEach(async (barcode) => {
    await page.getByText(barcode).first().waitFor();
  });
});

test('Settings - Admin - Unauthorized', async ({ page }) => {
  // Try to access "admin" page with a non-staff user
  await doQuickLogin(page, 'allaccess', 'nolimits');

  await navigate(page, 'settings/admin/');
  await page.waitForURL('**/settings/admin/**');

  // Should get a permission denied message
  await page.getByText('Permission Denied').waitFor();
  await page
    .getByRole('button', { name: 'Return to the index page' })
    .waitFor();

  // Try to access user settings page (should be accessible)
  await navigate(page, 'settings/user/');
  await page.waitForURL('**/settings/user/**');

  await loadTab(page, 'Display Options');
  await loadTab(page, 'Account');

  // Try to access global settings page
  await navigate(page, 'settings/system/');
  await page.waitForURL('**/settings/system/**');

  await page.getByText('Permission Denied').waitFor();
  await page
    .getByRole('button', { name: 'Return to the index page' })
    .waitFor();
});

// Test for user auth configuration
test('Settings - Auth - Email', async ({ page }) => {
  await doQuickLogin(page, 'allaccess', 'nolimits');
  await navigate(page, 'settings/user/');

  await loadTab(page, 'Security');

  await page.getByText('Currently no email addresses are registered').waitFor();
  await page.getByLabel('email-address-input').fill('test-email@domain.org');
  await page.getByLabel('email-address-submit').click();

  await page.getByText('Unverified', { exact: true }).waitFor();
  await page.getByLabel('test-email@domain.').click();
  await page.getByRole('button', { name: 'Make Primary' }).click();
  await page.getByText('Primary', { exact: true }).waitFor();
  await page.getByRole('button', { name: 'Remove' }).click();

  await page.getByText('Currently no email addresses are registered').waitFor();

  await page.waitForTimeout(2500);
});
