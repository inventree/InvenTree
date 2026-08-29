import { createApi } from './api.js';
import { expect, test } from './baseFixtures.js';
import { logoutUrl, mockSsoUser } from './defaults.js';
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
// Remove any account left over from a previous run - including one that
// failed partway, before its own cleanup could execute - since an existing
// SocialAccount link makes allauth log straight in instead of hitting the
// pending 'provider_signup' flow this test exists to cover.
async function deleteMockSsoUser() {
  const api = await createApi({});
  // user/ is unpaginated by default (no PAGE_SIZE configured) - returns a
  // plain array rather than a { results: [...] } envelope.
  const users = await api
    .get(`user/?search=${mockSsoUser.username}`)
    .then((response) => response.json());
  const existing = users.find(
    (user: any) => user.username === mockSsoUser.username
  );
  if (existing) {
    await api.delete(`user/${existing.pk}/`);
  }
}

test.beforeEach(deleteMockSsoUser);
test.afterEach(deleteMockSsoUser);

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
  const api = await createApi({});
  const users = await api
    .get(`user/?search=${mockSsoUser.username}`)
    .then((response) => response.json());
  expect(
    users.find((user: any) => user.username === mockSsoUser.username)
  ).toBeUndefined();
});
