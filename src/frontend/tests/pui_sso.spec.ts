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
test('SSO - Complete registration for a new SSO user', async ({ page }) => {
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

  // Clean up the created account, so the test can be re-run locally
  const api = await createApi({});
  const { results } = await api
    .get(`user/?search=${mockSsoUser.username}`)
    .then((response) => response.json());
  const created = results.find(
    (user: any) => user.username === mockSsoUser.username
  );

  expect(created).toBeDefined();
  await api.delete(`user/${created.pk}/`);
});
