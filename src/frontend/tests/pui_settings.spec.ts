import { expect, test } from './baseFixtures.js';
import { apiUrl } from './defaults.js';
import { getRowFromCell, loadTab, navigate } from './helpers.js';
import { doCachedLogin } from './login.js';
import { setPluginState, setSettingState } from './settings.js';

/**
 * Adjust language and color settings
 *
 * TODO: Reimplement this - without logging out a cached user
 */
// test('Settings - Language / Color', async ({ browser }) => {
//   const page = await doCachedLogin(browser);

//   await page.getByRole('button', { name: 'Ally Access' }).click();
//   await page.getByRole('menuitem', { name: 'Logout' }).click();
//   await page.getByRole('button', { name: 'Send me an email' }).click();
//   await page.getByLabel('Language toggle').click();
//   await page.getByLabel('Select language').first().click();
//   await page.getByRole('option', { name: 'German' }).click();
//   await page.waitForTimeout(200);

//   await page.getByRole('button', { name: 'Benutzername und Passwort' }).click();
//   await page.getByPlaceholder('Ihr Benutzername').click();
//   await page.getByPlaceholder('Ihr Benutzername').fill('admin');
//   await page.getByPlaceholder('Ihr Benutzername').press('Tab');
//   await page.getByPlaceholder('Dein Passwort').fill('inventree');
//   await page.getByRole('button', { name: 'Anmelden' }).click();
//   await page.waitForTimeout(200);

//   await page.getByRole('tab', { name: 'Dashboard' }).click();
//   await page.waitForURL('**/web/home');
// });

test('Settings - User theme', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    username: 'allaccess',
    password: 'nolimits'
  });

  await page.waitForLoadState('networkidle');

  await page.getByRole('button', { name: 'Ally Access' }).click();
  await page.getByRole('menuitem', { name: 'Account settings' }).click();

  // loader
  await page.getByRole('textbox', { name: 'Loader Type Selector' }).click();
  await page.getByRole('option', { name: 'Oval' }).click();
  await page.getByRole('textbox', { name: 'Loader Type Selector' }).click();
  await page.getByRole('option', { name: 'Bars' }).click();

  // dark / light mode
  await page
    .getByRole('row', { name: 'Color Mode' })
    .getByRole('button')
    .click();
  await page
    .getByRole('row', { name: 'Color Mode' })
    .getByRole('button')
    .click();

  // colors
  await testColorPicker(page, 'Color Picker White');
  await testColorPicker(page, 'Color Picker Black');

  await page.waitForTimeout(500);

  await page.getByLabel('Reset Black Color').click();
  await page.getByLabel('Reset White Color').click();

  // radius
  await page
    .locator('div')
    .filter({ hasText: /^xssmmdlgxl$/ })
    .nth(2)
    .click();

  // primary
  await page.getByLabel('#fab005').click();
  await page.getByLabel('#228be6').click();
});

test('Settings - User', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    username: 'allaccess',
    password: 'nolimits',
    url: 'settings/user/'
  });

  await loadTab(page, 'Account');
  await page.getByText('Account Details').waitFor();
  await page.getByText('Profile Details').waitFor();

  await loadTab(page, 'Security');
  await page.getByRole('button', { name: 'Single Sign On' }).waitFor();
  await page.getByRole('button', { name: 'Access Tokens' }).waitFor();

  await loadTab(page, 'Display Options');
  await page
    .getByText('The navbar position is fixed to the top of the screen')
    .waitFor();
  await page.getByText('Escape Key Closes Forms').waitFor();

  await loadTab(page, 'Search');
  await page.getByText('Whole Word Search').waitFor();
  await page.getByText('Hide Unavailable Stock Items').waitFor();

  await loadTab(page, 'Notifications');
  await page
    .getByRole('button', { name: 'InvenTree Email Notifications' })
    .waitFor();

  await loadTab(page, 'Reporting');
  await page.getByText('Inline report display').waitFor();

  // Toggle boolean setting
  await page
    .getByLabel('setting-LABEL_INLINE-wrapper')
    .locator('span')
    .nth(1)
    .click();

  await loadTab(page, 'Plugin Settings');
  await page
    .getByRole('button', { name: 'InvenTree Email Notifications' })
    .waitFor();
});

test('Settings - Global', async ({ browser, request }) => {
  const page = await doCachedLogin(browser, {
    username: 'steven',
    password: 'wizardstaff',
    url: 'settings/system/'
  });

  // Ensure the "slack" notification plugin is enabled
  // This is to ensure it is visible in the "notification" settings tab
  await setPluginState({
    request,
    plugin: 'inventree-slack-notification',
    state: true
  });

  await loadTab(page, 'Server');

  // edit some settings here
  await page
    .getByRole('button', { name: 'edit-setting-INVENTREE_COMPANY_NAME' })
    .click();
  await page
    .getByRole('textbox', { name: 'text-field-value' })
    .fill('some data');
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Toggle a boolean setting
  await page
    .getByLabel('setting-INVENTREE_ANNOUNCE_ID-wrapper')
    .locator('span')
    .nth(1)
    .click();
  await page
    .getByText('Setting INVENTREE_ANNOUNCE_ID updated successfully')
    .waitFor();
  await page
    .getByLabel('setting-INVENTREE_ANNOUNCE_ID-wrapper')
    .locator('span')
    .nth(1)
    .click();

  await loadTab(page, 'Authentication');
  await loadTab(page, 'Barcodes');
  await loadTab(page, 'Pricing');
  await loadTab(page, 'Parts');
  await loadTab(page, 'Stock', true);
  await loadTab(page, 'Stock History');

  await loadTab(page, 'Notifications');
  await page
    .getByText(
      'The settings below are specific to each available notification method'
    )
    .waitFor();

  await page
    .getByRole('button', { name: 'InvenTree Slack Notifications' })
    .click();
  await page.getByText('Slack incoming webhook url').waitFor();
  await page
    .getByText('URL that is used to send messages to a slack channel')
    .waitFor();

  await loadTab(page, 'Plugin Settings');
  await page
    .getByText('The settings below are specific to each available plugin')
    .waitFor();
  await page
    .getByRole('button', { name: 'InvenTree Barcodes Provides' })
    .waitFor();
  await page
    .getByRole('button', { name: 'InvenTree PDF label printer' })
    .waitFor();
  await page
    .getByRole('button', { name: 'InvenTree Slack Notifications' })
    .waitFor();
});

test('Settings - Admin', async ({ browser }) => {
  // Note here we login with admin access
  const page = await doCachedLogin(browser, {
    username: 'admin',
    password: 'inventree'
  });

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
  await loadTab(page, 'Authentication');
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

test('Settings - Admin - Barcode History', async ({ browser, request }) => {
  // Login with admin credentials
  const page = await doCachedLogin(browser, {
    username: 'admin',
    password: 'inventree'
  });

  // Ensure that the "save scans" setting is enabled
  await setSettingState({
    request: request,
    setting: 'BARCODE_STORE_RESULTS',
    value: true
  });

  // Scan some barcodes (via API calls)
  const barcodes = ['ABC1234', 'XYZ5678', 'QRS9012'];

  for (let i = 0; i < barcodes.length; i++) {
    const barcode = barcodes[i];
    const url = new URL('barcode/', apiUrl).toString();
    await request.post(url, {
      data: {
        barcode: barcode
      },
      timeout: 5000,
      headers: {
        Authorization: `Basic ${btoa('admin:inventree')}`
      }
    });
  }

  await page.getByRole('button', { name: 'admin' }).click();
  await page.getByRole('menuitem', { name: 'Admin Center' }).click();
  await loadTab(page, 'Barcode Scans');

  await page.waitForTimeout(500);

  // Barcode history is displayed in table
  barcodes.forEach(async (barcode) => {
    await page.getByText(barcode).first().waitFor();
  });
});

test('Settings - Admin - Unauthorized', async ({ browser }) => {
  // Try to access "admin" page with a non-staff user
  const page = await doCachedLogin(browser, {
    username: 'allaccess',
    password: 'nolimits',
    url: 'settings/admin/'
  });

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
test('Settings - Auth - Email', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    username: 'allaccess',
    password: 'nolimits',
    url: 'settings/user/'
  });

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
});

async function testColorPicker(page, ref: string) {
  const element = page.getByLabel(ref);
  await element.click();
  const box = (await element.boundingBox())!;
  await page.mouse.click(box.x + box.width / 2, box.y + box.height + 25);
  await page.getByText('Color Mode').click();
}
