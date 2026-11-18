/**
 * Tests for the "Admin Center" management tables.
 *
 * These tests exercise the create / edit / delete flows (and detail drawers)
 * for the user, group, custom state, email and identity management panels.
 */

import type { Page } from '@playwright/test';
import { createApi } from './api.js';
import { expect, generateUUID, test } from './baseFixtures.js';
import { adminuser } from './defaults.js';
import { clickOnRowMenu, loadTab, tableSearch } from './helpers.js';
import { doCachedLogin } from './login.js';

// Return the accordion control with the given title
const accordion = (page: Page, name: string) =>
  page.locator('.mantine-Accordion-control', {
    has: page.getByText(name, { exact: true })
  });

// Expand an accordion item (if it is not already expanded)
const openAccordion = async (page: Page, name: string) => {
  const control = accordion(page, name).first();
  await control.waitFor();
  if ((await control.getAttribute('aria-expanded')) !== 'true') {
    await control.click();
  }
};

test('Admin - Users and Groups', async ({ browser }) => {
  const suffix = generateUUID().slice(0, 8);
  const groupName = `pw-group-${suffix}`;
  const userName = `pw-user-${suffix}`;

  const page = await doCachedLogin(browser, {
    user: adminuser,
    url: 'settings/admin/user'
  });

  // Create a new group
  await openAccordion(page, 'Groups');
  await page.getByLabel('action-button-add-group').click();
  await page.getByLabel('text-field-name', { exact: true }).fill(groupName);
  await page.getByRole('button', { name: 'Submit' }).click();

  // Open the group detail drawer
  await page.getByRole('cell', { name: groupName, exact: true }).click();
  await page.getByText('Edit Group').first().waitFor();
  await page.getByText('Group Details').waitFor();

  // Edit the group roles
  await openAccordion(page, 'Group Roles');
  const partRow = page.getByRole('row', { name: /^Parts/ }).first();
  await partRow.getByRole('checkbox').nth(0).check();
  await partRow.getByRole('checkbox').nth(1).check();

  // Reset the changes, then make them again and save
  await page.getByRole('button', { name: 'Reset', exact: true }).click();
  await partRow.getByRole('checkbox').nth(0).check();
  await partRow.getByRole('checkbox').nth(2).check();
  await page.getByRole('button', { name: 'Save', exact: true }).click();
  await page.getByText('Group roles updated').first().waitFor();

  // Close the drawer
  await page.keyboard.press('Escape');
  await page.waitForTimeout(250);

  // Create a new user
  await openAccordion(page, 'Users');
  await page.getByLabel('action-button-add-user').click();
  await page.getByLabel('text-field-username').fill(userName);
  await page.getByLabel('text-field-email').fill(`${userName}@example.org`);
  await page.getByLabel('text-field-first_name').fill('Play');
  await page.getByLabel('text-field-last_name').fill('Wright');
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Added user').first().waitFor();

  // Open the user detail drawer
  const users = page.getByRole('region', { name: 'Users' });
  await users.getByLabel('table-search-input').fill(userName);
  await page.waitForTimeout(600);
  await page.waitForLoadState('networkidle');
  await page.getByRole('cell', { name: userName, exact: true }).click();
  await page.getByText('Edit User').first().waitFor();
  await page.getByText('User Details').waitFor();

  // Assign the new group to the user via the transfer list
  await openAccordion(page, 'User Groups');
  const groupItem = page
    .getByLabel('User Groups')
    .getByText(groupName, { exact: true });

  // Move all items across, and back again
  await page.getByLabel('transfer-all-right').click();
  await page.getByLabel('transfer-all-left').click();

  // Select a single item and move it across, then back, then across again
  // Note: items remain selected after being transferred
  await groupItem.click();
  await page.getByLabel('transfer-selected-right').click();
  await page.getByLabel('transfer-selected-left').click();
  await page.getByLabel('transfer-selected-right').click();
  await page.getByRole('button', { name: 'Save', exact: true }).click();
  await page.getByText('User groups updated successfully').first().waitFor();

  await page.keyboard.press('Escape');
  await page.waitForTimeout(250);

  // Lock and unlock the user via the row actions
  const userCell = page.getByRole('cell', { name: userName, exact: true });
  await clickOnRowMenu(userCell);
  await page.getByRole('menuitem', { name: 'Lock user' }).click();
  await page.getByText('User updated successfully').first().waitFor();

  await clickOnRowMenu(userCell);
  await page.getByRole('menuitem', { name: 'Unlock user' }).click();
  await page.waitForLoadState('networkidle');

  // Edit via row action (opens the drawer)
  await clickOnRowMenu(userCell);
  await page.getByRole('menuitem', { name: 'Edit' }).click();
  await page.getByText('User Details').waitFor();
  await page.keyboard.press('Escape');
  await page.waitForTimeout(250);

  // Delete the user
  await clickOnRowMenu(userCell);
  await page.getByRole('menuitem', { name: 'Delete' }).click();
  await page.getByRole('button', { name: 'Delete' }).click();
  await page.getByText('User deleted').first().waitFor();

  // Cleanup: delete the group via the API
  const api = await createApi({});
  const groups = await api
    .get('user/group/', { params: { search: groupName } })
    .then((res) => res.json());

  for (const group of groups.results ?? groups) {
    if (group.name == groupName) {
      await api.delete(`user/group/${group.pk}/`);
    }
  }
});

test('Admin - Custom States', async ({ browser }) => {
  const suffix = generateUUID().slice(0, 6);
  const name = `PW_STATE_${suffix.toUpperCase()}`;
  const key = 4000 + Math.floor(Math.random() * 1000);

  const page = await doCachedLogin(browser, {
    user: adminuser,
    url: 'settings/admin/custom-states'
  });

  await page.getByLabel('action-button-add-state').click();
  await page.getByLabel('choice-field-reference_status').click();
  await page.getByRole('option', { name: 'StockStatus', exact: true }).click();
  await page.getByLabel('choice-field-logical_key').click();
  await page.getByRole('option', { name: 'Damaged' }).click();
  await page.getByLabel('number-field-key').fill(`${key}`);
  await page.getByLabel('text-field-name', { exact: true }).fill(name);
  await page.getByLabel('text-field-label').fill(`PW ${suffix}`);
  await page.getByLabel('related-field-model').fill('stock item');
  await page.getByRole('option').first().click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.waitForLoadState('networkidle');

  await tableSearch(page, name);
  const cell = page.getByRole('cell', { name, exact: true });
  await cell.waitFor();

  // Edit
  await clickOnRowMenu(cell);
  await page.getByRole('menuitem', { name: 'Edit' }).click();
  await page.getByLabel('text-field-label').fill(`PW Edit ${suffix}`);
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByRole('cell', { name: `PW Edit ${suffix}` }).waitFor();

  // Duplicate (then cancel)
  await clickOnRowMenu(cell);
  await page.getByRole('menuitem', { name: 'Duplicate' }).click();
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Delete
  await clickOnRowMenu(cell);
  await page.getByRole('menuitem', { name: 'Delete' }).click();
  await page.getByRole('button', { name: 'Delete' }).click();
  await expect(page.getByRole('cell', { name, exact: true })).toHaveCount(0);
});

test('Admin - Misc Panels', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    user: adminuser,
    url: 'settings/admin/email'
  });

  // Email management panel
  await page.getByText('Email Messages').waitFor();
  await page.getByLabel('action-button-send-test-email').click();
  await page.getByRole('button', { name: 'Submit' }).waitFor();
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Note templates
  await loadTab(page, 'Note Templates');
  await page
    .getByText('Note templates can be used to create pre-defined notes')
    .waitFor();
});

test('Admin - Identity Federation', async ({ browser }) => {
  const appName = `pw-oidc-${generateUUID().slice(0, 6)}`;

  const page = await doCachedLogin(browser, {
    user: adminuser,
    url: 'settings/admin/identity'
  });

  await page.getByText('SCIM allows an external Identity Provider').waitFor();

  // Enable SCIM, which displays the secret once
  await page.getByRole('button', { name: 'Enable SCIM' }).click();
  await page.getByText('SCIM Bearer Secret').waitFor();
  await page.getByText('This secret is only shown once').waitFor();
  await page.keyboard.press('Escape');

  // Rotate the secret
  await page.getByRole('button', { name: 'Rotate Secret' }).click();
  await page.getByText('SCIM Bearer Secret').waitFor();
  await page.keyboard.press('Escape');

  // Disable SCIM again
  await page.getByRole('button', { name: 'Disable SCIM' }).click();
  await page.getByRole('button', { name: 'Enable SCIM' }).waitFor();

  // Open (and cancel) the generic + SAML application forms
  await openAccordion(page, 'Single Sign-On (SSO)');
  await page.getByRole('button', { name: 'Add Generic App' }).click();
  await page.getByRole('button', { name: 'Cancel' }).click();
  await page.getByRole('button', { name: 'Add SAML App' }).click();
  await page.getByText('Identity Provider Settings').first().waitFor();
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Create an OIDC application
  await page.getByRole('button', { name: 'Add OIDC App' }).click();
  await page.getByLabel('text-field-name', { exact: true }).fill(appName);
  await page.getByLabel('text-field-client_id').fill('pw-client');
  await page.getByLabel('text-field-secret').fill('pw-secret');
  await page
    .getByLabel('text-field-server_url')
    .fill('https://sso.example.org/');
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('OIDC Callback URL').waitFor();
  await page.keyboard.press('Escape');

  // Edit, then delete the application
  const cell = page.getByRole('cell', { name: appName, exact: true });
  await clickOnRowMenu(cell);
  await page.getByRole('menuitem', { name: 'Edit' }).click();
  await page.getByRole('button', { name: 'Cancel' }).click();

  await clickOnRowMenu(cell);
  await page.getByRole('menuitem', { name: 'Delete' }).click();
  await page.getByRole('button', { name: 'Delete' }).click();
  await expect(cell).toHaveCount(0);
});

test('Admin - Error Reports', async ({ browser }) => {
  const api = await createApi({});
  const response = await api.get('error-report/', { params: { limit: 1 } });
  expect(response.status()).toBe(200);
  const data = await response.json();

  const page = await doCachedLogin(browser, {
    user: adminuser,
    url: 'settings/admin/errors'
  });

  await page.waitForLoadState('networkidle');

  if ((data.count ?? data.length) > 0) {
    // Open the detail drawer for the first error
    await page.locator('table tbody tr').first().click();
    await page.getByText('Error Details').waitFor();
    await page.getByRole('rowheader', { name: 'Traceback' }).waitFor();
    await page.keyboard.press('Escape');
  }
});
