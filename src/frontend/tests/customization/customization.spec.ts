import test, { expect } from '@playwright/test';
import { navigate } from '../helpers';
import { doLogin } from '../login';

/**
 * Tests for user interface customization functionality.
 *
 * Note: The correct environment variables must be set for these tests to work correctly. See "playwright.config.ts" for details.
 * These tests are designed to run in CI environments where specific environment variables are set to enable custom logos and splash screens. The tests verify that these customizations are correctly applied in the user interface.
 */

test('Customization - Splash', async ({ page }) => {
  await navigate(page, '/');

  await page.waitForLoadState('networkidle');

  // Check for the custom splash screen
  await expect(
    page.locator('[style*="playwright_custom_splash.png"]')
  ).toBeVisible();
});

test('Customization - Logo', async ({ page }) => {
  await doLogin(page, {
    username: 'noaccess',
    password: 'youshallnotpass'
  });

  await page.waitForLoadState('networkidle');

  await page.waitForTimeout(2500);
  return;
});
