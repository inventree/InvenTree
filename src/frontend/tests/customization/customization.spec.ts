import { expect, test } from '../baseFixtures';
import { navigate } from '../helpers';

/**
 * Tests for user interface customization functionality.
 *
 * Note: The correct environment variables must be set for these tests to work correctly. See "playwright.config.ts" for details.
 * These tests are designed to run in CI environments where specific environment variables are set to enable custom logos and splash screens.
 * The tests verify that these customizations are correctly applied in the user interface.
 *
 * If you are running these tests locally, ensure that you have the appropriate environment variables set to enable the customizations.
 * You may need to modify the "webServer" configuration in "playwright.config.ts" to include the necessary environment variables for local testing.
 *
 */

test('Customization - Splash', async ({ page }) => {
  await navigate(page, '/');

  await page.waitForLoadState('networkidle');

  // Check for the custom splash screen
  await expect(
    page.locator('[style*="playwright_custom_splash.png"]')
  ).toBeVisible();
});
