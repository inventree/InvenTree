import { createApi } from '../api.js';
import { expect, generateUUID, test } from '../baseFixtures.js';
import { stevenuser } from '../defaults.js';
import { loadTab, navigate } from '../helpers.js';
import { doCachedLogin } from '../login.js';
import { setSettingState } from '../settings.js';

test('Core User/Group/Contact', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  // groups
  await navigate(page, '/core');
  await page.getByText('System Overview', { exact: true }).first().click();
  await loadTab(page, 'Groups');
  await page.getByRole('cell', { name: 'all access' }).click();
  await page.getByText('Group: all access', { exact: true }).click();
  await page.getByLabel('breadcrumb-1-groups').click();

  // users
  await loadTab(page, 'Users');
  await page.getByRole('cell', { name: 'admin', exact: true }).click();
  await page.getByText('User: admin', { exact: true }).waitFor();
  await page.getByLabel('User Details').waitFor();
  await page.getByLabel('breadcrumb-1-users').click();

  // contacts
  await loadTab(page, 'Contacts');
  await page.getByRole('cell', { name: 'Adrian Briggs' }).waitFor();
});

test('Core - User Profile', async ({ browser }) => {
  const suffix = generateUUID().slice(0, 8);
  const position = `Position ${suffix}`;
  const location = `Location ${suffix}`;

  await setSettingState({ setting: 'DISPLAY_PROFILE_INFO', value: true });

  // Find the primary key of the test user
  const api = await createApi({
    username: stevenuser.username,
    password: stevenuser.testcred
  });
  const me = await (await api.get('user/me/')).json();

  const page = await doCachedLogin(browser, { user: stevenuser });

  // Edit the user profile via the account settings page
  await navigate(page, 'settings/user/account');
  await page.getByText('Account Details').waitFor();
  await page.getByRole('button', { name: 'Edit Profile' }).click();

  await page.getByLabel('text-field-position').fill(position);
  await page.getByLabel('text-field-location').fill(location);
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Profile details updated').waitFor();

  // The profile information is displayed on the user detail page
  await navigate(page, `core/user/${me.pk}/`);
  await page
    .getByText(`User: ${stevenuser.username}`, { exact: true })
    .waitFor();
  await page.getByText('User Profile').waitFor();
  await page.getByText(position, { exact: true }).waitFor();
  await page.getByText(location, { exact: true }).waitFor();

  // The user (and profile) is also shown in the preview drawer
  let response = await api.patch('settings/user/ENABLE_PREVIEW_PANEL/', {
    data: { value: true }
  });
  expect(response.status()).toBe(200);

  // Reload the page (to fetch the updated user setting)
  await navigate(page, '/core');
  await loadTab(page, 'Users');
  await page
    .getByRole('cell', { name: stevenuser.username, exact: true })
    .click();
  await page.getByText(`User - ${stevenuser.username}`).waitFor();
  await expect(page.getByText('No preview available')).toHaveCount(0);
  await page.getByText(position, { exact: true }).waitFor();
  await page.keyboard.press('Escape');

  response = await api.patch('settings/user/ENABLE_PREVIEW_PANEL/', {
    data: { value: false }
  });
  expect(response.status()).toBe(200);

  // Disable the display of profile information
  await navigate(page, `core/user/${me.pk}/`);
  await setSettingState({ setting: 'DISPLAY_PROFILE_INFO', value: false });

  await page.reload();
  await page
    .getByText(`User: ${stevenuser.username}`, { exact: true })
    .waitFor();
  await page.getByText('User Information').waitFor();
  await expect(page.getByText('User Profile')).toHaveCount(0);
  await expect(page.getByText(position, { exact: true })).toHaveCount(0);

  // Restore the original state
  await setSettingState({ setting: 'DISPLAY_PROFILE_INFO', value: true });

  response = await api.patch('user/me/profile/', {
    data: { position: '', location: '' }
  });
  expect(response.status()).toBe(200);
});
