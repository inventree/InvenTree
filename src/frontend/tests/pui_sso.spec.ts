import { createApi } from './api.js';
import { expect, test } from './baseFixtures.js';
import { apiUrl, logoutUrl, mockSsoUser } from './defaults.js';
import { navigate } from './helpers.js';
import { setSettingState } from './settings.js';

/*
 * End-to-end coverage for logging in via SSO as a brand-new user.
 *
 * django-allauth leaves this scenario as a pending 'provider_signup' auth
 * flow rather than a completed login - see checkLoginState() in
 * src/functions/auth.tsx and src/pages/Auth/ProviderSignup.tsx. This test
 * drives the real SSO handshake against the mock OIDC provider started in
 * playwright.config.ts (playwright/mock-oidc-server.mjs), rather than
 * stubbing network responses, so it actually exercises the backend's
 * authorization-code exchange and pending-flow logic, not just the new
 * frontend page in isolation.
 */
// Every throwaway username any test in this file creates - kept in one
// place so cleanup can't miss one.
const TEST_USERNAMES = [
  mockSsoUser.username,
  'existingemailuser',
  'ssoconnecttest'
];

async function findUserByUsername(username: string): Promise<any> {
  const api = await createApi({});
  const data = await api
    .get(`user/?search=${encodeURIComponent(username)}`)
    .then((response) => response.json());
  // user/ is unpaginated by default (no PAGE_SIZE configured) - returns a
  // plain array - but fall back to a { results: [...] } envelope too, in
  // case pagination is ever turned on for it.
  const users = Array.isArray(data) ? data : (data?.results ?? []);
  return users.find((user: any) => user.username === username);
}

async function deleteUserByUsername(username: string) {
  const existing = await findUserByUsername(username);
  if (existing) {
    const api = await createApi({});
    await api.delete(`user/${existing.pk}/`);
  }
}

// Remove any account left over from a previous run - including one that
// failed partway, before its own cleanup could execute (a Playwright test
// timeout aborts the test function rather than waiting for an in-flight
// `finally` block to complete). An existing SocialAccount link in
// particular makes allauth log straight in instead of hitting the pending
// 'provider_signup' flow most of these tests exist to cover - and a leftover
// local user makes the next run's own creation of it fail outright.
async function cleanupTestUsers() {
  for (const username of TEST_USERNAMES) {
    await deleteUserByUsername(username);
  }
}

test.beforeEach(cleanupTestUsers);
test.afterEach(cleanupTestUsers);

/*
 * Create a throwaway local (non-SSO) user for tests that need one already
 * sitting in the database - e.g. an existing account colliding with the
 * mock SSO identity's username/email. Admin-created users get a random
 * password, so a known one is set separately wherever a test needs to log
 * in as this user directly.
 */
async function createLocalUser({
  username,
  email,
  password
}: {
  username: string;
  email: string;
  password?: string;
}) {
  const api = await createApi({});
  const user = await api
    .post('user/', {
      data: { username, email, first_name: 'Test', last_name: 'Fixture' }
    })
    .then((response) => response.json());

  if (password) {
    await api.patch(`user/${user.pk}/set-password/`, {
      data: { password, override_warning: true }
    });
  }

  return user;
}

async function deleteUser(pk: number) {
  const api = await createApi({});
  await api.delete(`user/${pk}/`);
}

test('SSO - Complete Registration', async ({ page }) => {
  // Allow SSO self-registration, but disable auto-signup - this is what
  // forces a brand-new SSO identity into the pending 'provider_signup' flow
  // instead of silently creating (or rejecting) an account.
  await setSettingState({ setting: 'LOGIN_ENABLE_SSO', value: true });
  await setSettingState({ setting: 'LOGIN_ENABLE_SSO_REG', value: true });
  await setSettingState({ setting: 'LOGIN_SIGNUP_SSO_AUTO', value: false });

  await navigate(page, logoutUrl, { waitUntil: 'load' });
  await page.waitForURL('**/web/login');

  // Follow the real redirect out to the mock IdP and back
  await page.getByRole('button', { name: 'Mock SSO' }).click();

  // No matching local account exists - the frontend should route to the
  // registration-completion page instead of bouncing back to '/login'
  await page.waitForURL('**/web/provider-signup');

  // Suggested username/email are prefilled from the mock IdP's claims
  await expect(page.getByLabel('provider-signup-username')).toHaveValue(
    mockSsoUser.username
  );
  await expect(page.getByLabel('provider-signup-email')).toHaveValue(
    mockSsoUser.email
  );

  await page.getByRole('button', { name: 'Complete Registration' }).click();

  // Registration completes, and the user is logged straight in
  await page.waitForURL(/\/web(\/home)?/);
  await page.getByRole('button', { name: 'navigation-menu' }).waitFor();
  await page
    .getByRole('button', {
      name: `${mockSsoUser.firstName} ${mockSsoUser.lastName}`
    })
    .waitFor();
});

test('SSO - Registration Disabled', async ({ page }) => {
  // Allow SSO login, but disable self-registration - a brand-new SSO
  // identity has no matching local account, and nothing should silently
  // create one.
  await setSettingState({ setting: 'LOGIN_ENABLE_SSO', value: true });
  await setSettingState({ setting: 'LOGIN_ENABLE_SSO_REG', value: false });

  await navigate(page, logoutUrl, { waitUntil: 'load' });
  await page.waitForURL('**/web/login');

  await page.getByRole('button', { name: 'Mock SSO' }).click();

  // django-allauth rejects the pending signup server-side (raises
  // SignupClosedException) before a 'provider_signup' flow is ever
  // recorded, so the frontend never reaches '/provider-signup' here - it
  // lands back on '/logged-in' with an 'error' query param appended (see
  // on_authentication_error() in allauth/headless/socialaccount/internal.py),
  // which LoggedIn.tsx must surface as a visible error instead of silently
  // bouncing back to a blank login page.
  await page.waitForURL('**/web/login');
  await page.getByText('SSO Login Failed').waitFor();
  await page.getByText('Registration via SSO is currently disabled.').waitFor();

  // No account should have been created
  expect(await findUserByUsername(mockSsoUser.username)).toBeUndefined();
});

test('SSO - Disabled', async ({ page }) => {
  // Master switch off, regardless of registration settings - the button
  // should disappear, and a direct attempt at the redirect endpoint
  // (bypassing the now-hidden button) must still be rejected server-side
  // by CustomSocialAccountAdapter.pre_social_login(), not just hidden
  // client-side.
  await setSettingState({ setting: 'LOGIN_ENABLE_SSO', value: false });

  await navigate(page, logoutUrl, { waitUntil: 'load' });
  await page.waitForURL('**/web/login');

  await expect(page.getByRole('button', { name: 'Mock SSO' })).toBeHidden();

  await page.evaluate(async (apiBase) => {
    // Populate the CSRF cookie, then submit the same redirect form
    // ProviderLogin() would have, driving the flow the hidden button would
    // otherwise start.
    await fetch(`${apiBase}auth/v1/auth/session`, { credentials: 'include' });
    const csrftoken = document.cookie
      .split('; ')
      .find((row) => row.startsWith('csrftoken='))
      ?.split('=')[1];

    const form = document.createElement('form');
    form.method = 'post';
    form.action = `${apiBase}auth/v1/auth/provider/redirect`;
    const fields: Record<string, string> = {
      provider: 'mock',
      callback_url: `${window.location.origin}/web/logged-in`,
      process: 'login',
      csrfmiddlewaretoken: csrftoken ?? ''
    };
    for (const [key, value] of Object.entries(fields)) {
      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = key;
      input.value = value;
      form.appendChild(input);
    }
    document.body.appendChild(form);
    form.submit();
  }, apiUrl);

  await page.waitForURL('**/web/login');
  await page.getByText('SSO Login Failed').waitFor();
  await page
    .getByText('You do not have permission to log in this way.')
    .waitFor();
});

test('SSO - Provider Signup Page With No Pending Signup', async ({ page }) => {
  // Loading '/provider-signup' with no pending signup in the session - e.g.
  // a direct visit, a bookmark, or a reload after the session has expired -
  // used to silently bounce back to a blank '/login' with zero explanation
  // (the server correctly returns 409, but the page ignored the status and
  // just navigated away). Regression test for that fix.
  await setSettingState({ setting: 'LOGIN_ENABLE_SSO', value: true });
  await setSettingState({ setting: 'LOGIN_ENABLE_SSO_REG', value: true });

  await navigate(page, logoutUrl, { waitUntil: 'load' });
  await page.waitForURL('**/web/login');

  await navigate(page, 'provider-signup', { waitUntil: 'load' });

  await page.waitForURL('**/web/login');
  await page.getByText('Registration Failed').waitFor();
  await page
    .getByText(
      'Your SSO sign-in session has expired. Please try logging in again.'
    )
    .waitFor();
});

test('SSO - Auto Signup', async ({ page }) => {
  // LOGIN_SIGNUP_SSO_AUTO's default value - a brand-new SSO identity should
  // be signed up and logged in automatically, with no confirmation step at
  // all. This is the most common real-world path, and the opposite of
  // 'SSO - Complete Registration' above (which explicitly disables this).
  await setSettingState({ setting: 'LOGIN_ENABLE_SSO', value: true });
  await setSettingState({ setting: 'LOGIN_ENABLE_SSO_REG', value: true });
  await setSettingState({ setting: 'LOGIN_SIGNUP_SSO_AUTO', value: true });

  await navigate(page, logoutUrl, { waitUntil: 'load' });
  await page.waitForURL('**/web/login');

  await page.getByRole('button', { name: 'Mock SSO' }).click();

  // Straight through to the dashboard - never touches '/provider-signup'
  await page.waitForURL(/\/web(\/home)?/);
  await page.getByRole('button', { name: 'navigation-menu' }).waitFor();
  await page
    .getByRole('button', {
      name: `${mockSsoUser.firstName} ${mockSsoUser.lastName}`
    })
    .waitFor();

  // The account was created using the claims from the mock IdP
  const created = await findUserByUsername(mockSsoUser.username);
  expect(created).toBeDefined();
  expect(created.email).toEqual(mockSsoUser.email);
});

test('SSO - Existing User Login', async ({ page }) => {
  // A second login as the same SSO identity should go straight through -
  // the SocialAccount is already linked from the first login, so none of
  // the new-user signup logic (or its own 'auto signup' gate) applies.
  await setSettingState({ setting: 'LOGIN_ENABLE_SSO', value: true });
  await setSettingState({ setting: 'LOGIN_ENABLE_SSO_REG', value: true });
  await setSettingState({ setting: 'LOGIN_SIGNUP_SSO_AUTO', value: true });

  // First login creates and links the account. Waiting for 'navigation-menu'
  // (not just the URL) matters here - '/\/web(\/home)?/' is unanchored and
  // also matches the transient '/web/logged-in' stop along the way, so a
  // bare waitForURL can resolve before the login has actually settled,
  // racing the setSettingState() call right after it.
  await navigate(page, logoutUrl, { waitUntil: 'load' });
  await page.waitForURL('**/web/login');
  await page.getByRole('button', { name: 'Mock SSO' }).click();
  await page.waitForURL(/\/web(\/home)?/);
  await page.getByRole('button', { name: 'navigation-menu' }).waitFor();

  // Disable auto-signup entirely - if this second login were mistakenly
  // treated as a new signup, it would now hit '/provider-signup' instead
  await setSettingState({ setting: 'LOGIN_SIGNUP_SSO_AUTO', value: false });

  await navigate(page, logoutUrl, { waitUntil: 'load' });
  await page.waitForURL('**/web/login');
  await page.getByRole('button', { name: 'Mock SSO' }).click();

  // Straight through again - no confirmation step for an already-linked account
  await page.waitForURL(/\/web(\/home)?/);
  await page.getByRole('button', { name: 'navigation-menu' }).waitFor();
});

test('SSO - Existing Local Account With Matching Email', async ({ page }) => {
  // A separate local account with the SAME email as the SSO identity, but
  // no linked SocialAccount, must not be silently merged into or
  // duplicated - django-allauth surfaces a clear validation error instead,
  // asking the user to log in normally and connect the SSO account there.
  await setSettingState({ setting: 'LOGIN_ENABLE_SSO', value: true });
  await setSettingState({ setting: 'LOGIN_ENABLE_SSO_REG', value: true });
  await setSettingState({ setting: 'LOGIN_SIGNUP_SSO_AUTO', value: false });

  const existing = await createLocalUser({
    username: 'existingemailuser',
    email: mockSsoUser.email
  });

  try {
    await navigate(page, logoutUrl, { waitUntil: 'load' });
    await page.waitForURL('**/web/login');
    await page.getByRole('button', { name: 'Mock SSO' }).click();

    // Still treated as a pending new signup - no auto-link by email
    await page.waitForURL('**/web/provider-signup');
    await page.getByRole('button', { name: 'Complete Registration' }).click();

    await page
      .getByText(
        'An account already exists with this email address. Please sign in to that account first, then connect your Mock SSO account.'
      )
      .waitFor();

    // No second/duplicate account was created
    expect(await findUserByUsername(mockSsoUser.username)).toBeUndefined();
  } finally {
    await deleteUser(existing.pk);
  }
});

test('SSO - Username Collision On Signup', async ({ page }) => {
  // The suggested username from the IdP collides with a different,
  // unrelated existing user - the signup form must surface that as a field
  // error rather than crashing or silently failing.
  await setSettingState({ setting: 'LOGIN_ENABLE_SSO', value: true });
  await setSettingState({ setting: 'LOGIN_ENABLE_SSO_REG', value: true });
  await setSettingState({ setting: 'LOGIN_SIGNUP_SSO_AUTO', value: false });

  const existing = await createLocalUser({
    username: mockSsoUser.username,
    email: 'someoneelse@example.org'
  });

  try {
    await navigate(page, logoutUrl, { waitUntil: 'load' });
    await page.waitForURL('**/web/login');
    await page.getByRole('button', { name: 'Mock SSO' }).click();
    await page.waitForURL('**/web/provider-signup');

    // The suggested username is still prefilled, even though it collides
    await expect(page.getByLabel('provider-signup-username')).toHaveValue(
      mockSsoUser.username
    );

    await page.getByRole('button', { name: 'Complete Registration' }).click();
    await page.getByText('A user with that username already exists.').waitFor();

    // Still on the signup page - no account was created or logged into
    await expect(page).toHaveURL(/\/web\/provider-signup/);
  } finally {
    await deleteUser(existing.pk);
  }
});

test('SSO - Connect Provider To Existing Account', async ({ page }) => {
  // An already-logged-in (non-SSO) user can link an SSO provider to their
  // account from Account Settings > Security - a separate entry point
  // (ProviderLogin(provider, 'connect')) from the login page's button.
  await setSettingState({ setting: 'LOGIN_ENABLE_SSO', value: true });

  const password = 'Test-Password-1234!';
  const user = await createLocalUser({
    username: 'ssoconnecttest',
    email: 'ssoconnecttest@example.org',
    password
  });

  try {
    await navigate(page, logoutUrl, { waitUntil: 'load' });
    await page.waitForURL('**/web/login');
    await page.getByLabel('login-username').fill(user.username);
    await page.getByLabel('login-password').fill(password);
    await page.getByRole('button', { name: 'Log In' }).click();
    // '/\/web(\/home)?/' is unanchored, so it also matches the transient
    // '/web/logged-in' stop along the way - wait for 'navigation-menu' too,
    // so the following navigate() isn't racing a still-settling login.
    await page.waitForURL(/\/web(\/home)?/);
    await page.getByRole('button', { name: 'navigation-menu' }).waitFor();

    await navigate(page, 'settings/user/security', {
      waitUntil: 'networkidle'
    });
    await page.getByText('Single Sign On').click();
    await page.getByRole('button', { name: 'Mock SSO' }).click();

    // Real redirect out to the mock IdP and back - lands on the dashboard,
    // not back on the settings page (get_connect_redirect_url() always
    // returns the frontend root)
    await page.waitForURL(/\/web(\/home)?/);
    await page.getByRole('button', { name: 'navigation-menu' }).waitFor();

    // Confirm the provider now shows as connected to this account
    await navigate(page, 'settings/user/security', {
      waitUntil: 'networkidle'
    });
    await page.getByText('Single Sign On').click();
    await page.getByText(`Mock SSO: ${mockSsoUser.email}`).waitFor();
  } finally {
    // Deleting the user cascades away the SocialAccount link too, so the
    // mock identity is unlinked again for other tests
    await deleteUser(user.pk);
  }
});
