/**
 * Tests for UI permissions checks
 */

import test from '@playwright/test';
import { clickOnRowMenu, loadTab } from './helpers';
import { doCachedLogin } from './login';

/**
 * Test the "admin" account
 * - This is a superuser account, so should have *all* permissions available
 */
test('Permissions - Admin', async ({ browser, request }) => {
  // Login, and start on the "admin" page
  const page = await doCachedLogin(browser, {
    username: 'admin',
    password: 'inventree',
    url: '/settings/admin/'
  });

  // Check for expected tabs
  await loadTab(page, 'Machines');
  await loadTab(page, 'Plugins');
  await loadTab(page, 'Users / Access');

  // Let's check creating a new user
  await page.getByLabel('action-button-add-user').click();
  await page.getByRole('button', { name: 'Submit' }).waitFor();
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Change password
  await clickOnRowMenu(
    await page.getByRole('cell', { name: 'Ian', exact: true })
  );
  await page.getByRole('menuitem', { name: 'Change Password' }).click();
  await page.getByLabel('text-field-password').fill('123');
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText("['This password is too short").waitFor();
  await page
    .locator('label')
    .filter({ hasText: 'Override warning' })
    .locator('div')
    .first()
    .click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Password updated').click();

  // Open profile
  await clickOnRowMenu(
    await page.getByRole('cell', { name: 'Ian', exact: true })
  );
  await page.getByRole('menuitem', { name: 'Open Profile' }).click();
  await page.getByText('User: ian', { exact: true }).click();
});

/**
 * Test the "reader" account
 * - This account is read-only, but should be able to access *most* pages
 */
test('Permissions - Reader', async ({ browser, request }) => {
  // Login, and start on the "admin" page
  const page = await doCachedLogin(browser, {
    username: 'reader',
    password: 'readonly',
    url: '/part/category/index/'
  });

  await loadTab(page, 'Category Details');
  await loadTab(page, 'Parts');

  // Navigate to a specific part
  await page.getByPlaceholder('Search').fill('Blue Chair');
  await page
    .getByRole('cell', { name: 'Thumbnail Blue Chair' })
    .locator('div')
    .first()
    .click();

  await page
    .getByLabel('Part Details')
    .getByText('A chair - with blue paint')
    .waitFor();

  // Printing actions *are* available to the reader account
  await page.getByLabel('action-menu-printing-actions').waitFor();

  // Check that the user *does not* have the part actions menu
  const actionsMenuVisible = await page
    .getByLabel('action-menu-part-actions')
    .isVisible({ timeout: 2500 });

  if (actionsMenuVisible) {
    throw new Error('Actions menu should not be visible for reader account');
  }

  // Navigate to the user / group info (via the navigation menu)
  await page.getByLabel('navigation-menu').click();
  await page.getByRole('button', { name: 'Users' }).click();
  await page.getByText('System Overview', { exact: true }).waitFor();
  await loadTab(page, 'Users');
  await loadTab(page, 'Groups');
  await page.getByRole('cell', { name: 'engineering' }).waitFor();

  // Go to the user profile page
  await page.getByRole('button', { name: 'Ronald Reader' }).click();
  await page.getByRole('menuitem', { name: 'Account Settings' }).click();

  await loadTab(page, 'Notifications');
  await loadTab(page, 'Display Options');
  await loadTab(page, 'Security');
  await loadTab(page, 'Account');

  await page.getByText('Account Details').waitFor();
  await page.getByText('Profile Details').waitFor();
});
