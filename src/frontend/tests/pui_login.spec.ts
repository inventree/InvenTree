import type { Page } from '@playwright/test';
import { TOTP } from 'otpauth';
import { expect, test } from './baseFixtures.js';
import { engineeruser, logoutUrl, noaccessuser } from './defaults.js';
import { navigate, openDetailAction } from './helpers.js';
import { doLogin } from './login.js';

const stripQueryAndHash = (url: string): string => {
  try {
    const parsed = new URL(url);
    return `${parsed.origin}${parsed.pathname}`;
  } catch {
    return url.split('?')[0].split('#')[0];
  }
};

const isScriptOrStyle = (resourceType: string): boolean => {
  return resourceType === 'script' || resourceType === 'stylesheet';
};

const isCriticalBundle = (url: string): boolean => {
  if (!/\.(js|css)$/i.test(url)) {
    return false;
  }

  if (/\.map$/i.test(url)) {
    return false;
  }

  if (/(@vite\/client|hot-update)/i.test(url)) {
    return false;
  }

  return /\/(assets|static)\//i.test(url);
};

const loginAndMeasure = async (page: Page): Promise<number> => {
  await navigate(page, logoutUrl, { waitUntil: 'load' });
  await page.waitForURL('**/web/login');

  await page.getByLabel('login-username').fill(noaccessuser.username);
  await page.getByLabel('login-password').fill(noaccessuser.testcred);

  const start = Date.now();
  await page.getByRole('button', { name: 'Log In' }).click();

  await page.getByRole('link', { name: 'Dashboard' }).waitFor();
  await page.getByRole('button', { name: 'navigation-menu' }).waitFor();
  await page.waitForURL(/\/web(\/home)?/);
  await page.waitForLoadState('networkidle');

  // Ensure dashboard has completely loaded
  await page.getByText('No Widgets Selected').waitFor();
  await page.getByRole('button', { name: 'Norman Nothington' }).waitFor();
  await page.waitForLoadState('networkidle');

  return Date.now() - start;
};

/**
 * Test various types of login failure
 */
test('Login - Failures', async ({ page }) => {
  const loginWithError = async ({
    msg,
    reload = true
  }: {
    msg?: string;
    reload?: boolean;
  }) => {
    await page.getByRole('button', { name: 'Log In' }).click();
    await page.getByText('Login failed', { exact: true }).waitFor();
    await page.getByText('Check your input and try again').first().waitFor();

    if (msg) {
      await page.getByText(msg).waitFor();
    }

    if (reload) {
      await page.reload();
    }
  };

  // Navigate to the 'login' page
  await navigate(page, logoutUrl);
  await expect(page).toHaveTitle(/^InvenTree.*$/);
  await page.waitForURL('**/web/login');

  // Attempt login with invalid credentials
  await page.getByLabel('login-username').fill('invalid user');
  await page.getByLabel('login-password').fill('invalid password');

  await loginWithError({
    msg: 'The username and/or password you specified are not correct'
  });

  // Attempt login with valid (but disabled) user
  await page.getByLabel('login-username').fill('ian');
  await page.getByLabel('login-password').fill('inactive');

  await loginWithError({});

  // Attempt login with no username
  await page.getByLabel('login-username').fill('');
  await page.getByLabel('login-password').fill('hunter2');

  await loginWithError({});

  // Attempt login with no password
  await page.getByLabel('login-username').fill('ian');
  await page.getByLabel('login-password').fill('');

  await loginWithError({});

  let tooManyAttempts = false;

  // Attempt login with incorrect password, multiple attempts
  for (let i = 0; i < 10; i++) {
    await page.getByLabel('login-username').fill('reader');
    await page.getByLabel('login-password').fill('readonlyx');
    await loginWithError({ reload: false });

    const text = await page.getByText('Too many failed login attempts', {
      exact: false
    });

    if (
      await expect(text)
        .toBeVisible({ timeout: 100 })
        .then(() => true)
        .catch(() => false)
    ) {
      tooManyAttempts = true;
      break;
    }

    await page.reload();
  }

  if (!tooManyAttempts) {
    await expect(tooManyAttempts).toEqual(true);
  }
});

// Check that page load times do not exceed thresholds for cold/warm/hot login scenarios
test('Login - Cold vs Warm vs Hot Load', async ({ page }) => {
  // Ensure a fresh state for the cold login measurement.
  await page.context().clearCookies();
  await navigate(page, logoutUrl, { waitUntil: 'load' });
  await page.waitForURL('**/web/login');
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  // Page load threshold values
  // Note: Vite server in dev mode is significantly slower than production build
  const COLD_MS_THRESHOLD: number = 5000;
  const WARM_MS_THRESHOLD: number = 4000;
  const HOT_MS_THRESHOLD: number = 3500;

  const coldMs = await loginAndMeasure(page);

  await navigate(page, logoutUrl, { waitUntil: 'load' });
  await page.waitForURL('**/web/login');

  const warmMs = await loginAndMeasure(page);

  console.log('Cold MS:', coldMs, 'Warm MS:', warmMs);
  expect(coldMs).toBeLessThan(COLD_MS_THRESHOLD);
  expect(warmMs).toBeLessThan(WARM_MS_THRESHOLD);

  // Perform a "hot" reload of the dashboard page, which should be faster than the warm login.
  const start = Date.now();
  await page.reload();
  // Ensure dashboard has completely loaded
  await page.getByText('No Widgets Selected').waitFor();
  await page.getByRole('button', { name: 'Norman Nothington' }).waitFor();
  await page.waitForLoadState('networkidle');

  const hotMs = Date.now() - start;

  console.log('Hot MS:', hotMs);
  expect(hotMs).toBeLessThan(HOT_MS_THRESHOLD);
});

// Check for JS/CSS request failures and duplicate critical bundles during login boot
test('Login - JS/CSS Boot Checks', async ({ page }) => {
  const failedResources: string[] = [];
  const criticalResourceCounts = new Map<string, number>();

  page.on('requestfailed', (request) => {
    if (!isScriptOrStyle(request.resourceType())) {
      return;
    }

    failedResources.push(
      `${request.resourceType()} ${request.url()} (${request.failure()?.errorText ?? 'request failed'})`
    );
  });

  page.on('requestfinished', async (request) => {
    if (!isScriptOrStyle(request.resourceType())) {
      return;
    }

    const response = await request.response();

    if (!response) {
      return;
    }

    const status = response.status();

    if (status >= 400) {
      failedResources.push(
        `${request.resourceType()} ${request.url()} (HTTP ${status})`
      );
    }

    const normalizedUrl = stripQueryAndHash(request.url());

    if (isCriticalBundle(normalizedUrl)) {
      const count = criticalResourceCounts.get(normalizedUrl) ?? 0;
      criticalResourceCounts.set(normalizedUrl, count + 1);
    }
  });

  await loginAndMeasure(page);

  const duplicateCriticalBundles = [...criticalResourceCounts.entries()]
    .filter(([, count]) => count > 1)
    .map(([url, count]) => `${url} x${count}`);

  expect(
    failedResources,
    `JS/CSS failures during login boot:\n${failedResources.join('\n')}`
  ).toEqual([]);
  expect(
    duplicateCriticalBundles,
    `Duplicate critical bundles during login boot:\n${duplicateCriticalBundles.join('\n')}`
  ).toEqual([]);
});

// Check page redirect after login
test('Login - Redirect on Login', async ({ page }) => {
  await navigate(page, logoutUrl, { waitUntil: 'load' });
  await page.waitForURL('**/web/login');

  await navigate(page, 'settings/user/account', { waitUntil: 'load' });
  await page.waitForURL('**/web/login');

  await page.getByLabel('login-username').fill(engineeruser.username);
  await page.getByLabel('login-password').fill(engineeruser.testcred);
  await page.getByRole('button', { name: 'Log In' }).click();

  await page.waitForURL('**/web/settings/user/account');
  await page.getByRole('button', { name: 'action-menu-account' }).waitFor();
  await page.getByRole('button', { name: 'Robert Shuruncle' }).waitFor();
});

// Test that login session persists across page reload
test('Login - Session Persistence', async ({ page }) => {
  await doLogin(page, {
    user: engineeruser
  });

  await page.getByText('Use the menu to add widgets').waitFor();
  await page.reload();
  await page.getByRole('button', { name: 'navigation-menu' }).waitFor();

  // Once we logout, the user session has been invalidated
  await navigate(page, logoutUrl, { waitUntil: 'load' });
  await page.waitForURL('**/web/login');

  await page.goBack();
  await page.waitForURL('**/web/login');
  await page.getByLabel('login-username').waitFor();
});

// Test login session with forced network errors
test('Login - Network Errors & Retry', async ({ page }) => {
  await navigate(page, logoutUrl, { waitUntil: 'load' });
  await page.waitForURL('**/web/login');

  await page.getByLabel('login-username').fill(engineeruser.username);
  await page.getByLabel('login-password').fill(engineeruser.testcred);

  const loginEndpoint = /auth\/login/;

  await page.route(loginEndpoint, (route) => {
    route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Simulated server failure' })
    });
  });

  const loginButton = page.getByRole('button', { name: 'Log In' });
  await loginButton.click();

  await page.getByText('Login failed (500)').waitFor();
  await page.getByText('Simulated server failure').waitFor();
  await expect(loginButton).toBeEnabled();

  await page.unroute(loginEndpoint);
  await loginButton.click();
  await page.getByRole('button', { name: 'navigation-menu' }).waitFor();

  await navigate(page, logoutUrl, { waitUntil: 'load' });
  await page.waitForURL('**/web/login');
  await page.getByLabel('login-username').fill(noaccessuser.username);
  await page.getByLabel('login-password').fill(noaccessuser.testcred);

  await page.route(loginEndpoint, (route) => {
    route.abort('internetdisconnected');
  });

  await loginButton.click();
  await page.getByText('Login failed').first().waitFor();
  await page.getByText('No response from server.').waitFor();
  await expect(loginButton).toBeEnabled();
  await page.getByLabel('login-username').waitFor();

  await page.unroute(loginEndpoint);
  await loginButton.click();
  await page.getByRole('button', { name: 'navigation-menu' }).waitFor();
});

// Check for exposed tokens or cookies after login, and ensure session cookie is secure
test('Login - Security Regression Checks', async ({ page }) => {
  await doLogin(page, {
    user: noaccessuser
  });

  const url = page.url();

  expect(url).not.toMatch(/[?&](token|access_token|refresh_token|jwt|auth)=/i);

  const storageData = await page.evaluate(() => {
    return {
      localStorageEntries: Object.entries(localStorage),
      sessionStorageEntries: Object.entries(sessionStorage)
    };
  });

  const suspiciousStorageEntries = [
    ...storageData.localStorageEntries,
    ...storageData.sessionStorageEntries
  ].filter(([key, value]) => {
    const combined = `${key} ${value}`;

    return (
      /(access_token|refresh_token|jwt|bearer)/i.test(combined) ||
      /^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(value)
    );
  });

  expect(suspiciousStorageEntries).toEqual([]);

  const cookies = await page.context().cookies();
  const sessionCookie = cookies.find((cookie) => cookie.name === 'sessionid');

  expect(sessionCookie).toBeDefined();
  expect(sessionCookie?.httpOnly).toBeTruthy();
  expect(['Lax', 'None', 'Strict']).toContain(sessionCookie?.sameSite ?? 'Lax');
});

// Check keyboard navigation of the login screen
test('Login - Keyboard Focus', async ({ page }) => {
  await navigate(page, logoutUrl, { waitUntil: 'load' });
  await page.waitForURL('**/web/login');

  const username = page.getByLabel('login-username');
  const password = page.getByLabel('login-password');

  await expect(username).toBeVisible();
  await expect(password).toBeVisible();

  await username.focus();
  await page.keyboard.type(noaccessuser.username);
  await page.keyboard.press('Tab');
  await expect(password).toBeFocused();
  await page.keyboard.type(noaccessuser.testcred);
  await page.keyboard.press('Enter');

  await page.getByRole('button', { name: 'navigation-menu' }).waitFor();

  await navigate(page, logoutUrl, { waitUntil: 'load' });
  await page.waitForURL('**/web/login');
  await page.getByRole('button', { name: 'Log In' }).click();
  await expect(page.getByLabel('login-username')).toBeFocused();
});

test('Login - Change Password', async ({ page }) => {
  await doLogin(page, {
    user: noaccessuser
  });

  // Navigate to the 'change password' page
  await navigate(page, 'settings/user/account', { waitUntil: 'networkidle' });

  await page.waitForTimeout(1000);
  await openDetailAction(page, 'account', 'change-password');

  // First attempt with some errors
  await page.getByLabel('password', { exact: true }).fill('youshallnotpass');
  await page.getByLabel('input-password-1').fill('12345');
  await page.getByLabel('input-password-2').fill('54321');
  await page.getByRole('button', { name: 'Confirm' }).click();
  await page.getByText('The two password fields didn’t match').waitFor();

  await page.getByLabel('input-password-2').clear();
  await page.getByLabel('input-password-2').fill('12345');
  await page.getByRole('button', { name: 'Confirm' }).click();

  await page.getByText('This password is too short').waitFor();
  await page.getByText('This password is entirely numeric').waitFor();

  await page.waitForTimeout(250);

  await page.getByLabel('password', { exact: true }).clear();
  await page.getByLabel('input-password-1').clear();
  await page.getByLabel('input-password-2').clear();

  await page.getByLabel('password', { exact: true }).fill('youshallnotpass');
  await page.getByLabel('input-password-1').fill('youshallnotpass');
  await page.getByLabel('input-password-2').fill('youshallnotpass');

  await page.getByRole('button', { name: 'Confirm' }).click();

  await page.getByText('Password Changed').waitFor();
  await page.getByText('The password was set successfully').waitFor();
});

// Tests for assigning MFA tokens to users
test('Login - MFA - TOTP', async ({ page }) => {
  await doLogin(page, {
    user: noaccessuser
  });

  await navigate(page, 'settings/user/security', { waitUntil: 'networkidle' });

  // Expand the MFA section
  await page
    .getByRole('button', { name: 'Multi-Factor Authentication' })
    .click();
  await page.getByRole('button', { name: 'add-factor-totp' }).click();

  // Ensure the user starts without any codes
  await page
    .getByText('No multi-factor tokens configured for this account')
    .waitFor();

  // Try to submit with an empty code
  await page.getByRole('textbox', { name: 'text-input-otp-code' }).fill('');
  await page.getByRole('button', { name: 'Submit', exact: true }).click();

  await page.getByText('This field is required.').waitFor();

  // Try to submit with an invalid secret
  await page
    .getByRole('textbox', { name: 'text-input-otp-code' })
    .fill('ABCDEF');
  await page.getByRole('button', { name: 'Submit', exact: true }).click();

  await page.getByText('Incorrect code.').waitFor();

  // Submit a valid code
  const secret = await page
    .getByLabel('otp-secret', { exact: true })
    .innerText();

  // Construct a TOTP code based on the secret
  const totp = new TOTP({
    secret: secret,
    digits: 6,
    period: 30
  });

  const token = totp.generate();

  await page.getByRole('textbox', { name: 'text-input-otp-code' }).fill(token);
  await page.getByRole('button', { name: 'Submit', exact: true }).click();
  await page.getByText('TOTP token registered successfully').waitFor();

  // View recovery codes
  await page.getByRole('button', { name: 'view-recovery-codes' }).click();
  await page
    .getByText('The following one time recovery codes are available')
    .waitFor();
  await page.getByRole('button', { name: 'Close' }).click();

  // Remove TOTP token
  await page.getByRole('button', { name: 'remove-totp' }).click();
  await page.getByRole('button', { name: 'Remove', exact: true }).click();

  await page.getByText('TOTP token removed successfully').waitFor();

  // And, once again there should be no configured tokens
  await page
    .getByText('No multi-factor tokens configured for this account')
    .waitFor();
});
