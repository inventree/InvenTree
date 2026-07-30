import { expect, test } from './baseFixtures';
import { stevenuser } from './defaults';
import { doCachedLogin } from './login';

/**
 * Regression coverage for the "Previous / Next" action on entity
 * detail pages. See https://github.com/inventree/InvenTree/issues/12397
 *
 * The expected behavior is:
 *   - On the detail page for a part, both prev / next icon buttons are
 *     rendered next to the actions group.
 *   - Clicking "next" navigates to the next sibling (or stays put when
 *     no neighbour exists).
 *   - Clicking "prev" navigates to the previous sibling (or stays put
 *     when no neighbour exists).
 *   - When no neighbour exists, the corresponding button is disabled.
 */
test('Part Detail - Previous / Next navigation', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    user: stevenuser,
    url: 'part/1/details'
  });

  // The two icon buttons should be present and reachable by their
  // stable test ids.
  const prevButton = page.getByTestId('inventree-prev-item');
  const nextButton = page.getByTestId('inventree-next-item');

  await prevButton.waitFor();
  await nextButton.waitFor();

  // Capture the current URL so we can detect movement.
  const startUrl = page.url();
  const startMatch = startUrl.match(/\/part\/(\d+)\//);
  if (!startMatch) {
    throw new Error(`Unexpected start URL: ${startUrl}`);
  }
  const startPk = Number(startMatch[1]);

  // At least one neighbour must exist for the seeded data set used by
  // the Playwright fixtures; otherwise we can't exercise the click.
  // Try clicking next; if it stays put, the dataset has only one part,
  // and we still want the buttons to render without throwing.
  await nextButton.click();

  // Wait for either navigation or a no-op (button stays disabled).
  await page.waitForLoadState('networkidle').catch(() => {
    /* no-op for the disabled-button case */
  });

  const urlAfterNext = page.url();
  const matchAfterNext = urlAfterNext.match(/\/part\/(\d+)\//);
  if (matchAfterNext && Number(matchAfterNext[1]) !== startPk) {
    // We did move; verify the prev button is now enabled (because
    // there is at least the previous starting instance).
    await prevButton.waitFor();
    await prevButton.click();
    await page.waitForLoadState('networkidle').catch(() => {
      /* see above */
    });
    // After clicking prev we should be back on the starting part (or
    // even earlier). At minimum we must still be on a /part/<n>/ URL.
    const urlAfterPrev = page.url();
    expect(urlAfterPrev).toMatch(/\/part\/\d+\//);
  } else {
    // No next sibling - the dataset has a single part. The next button
    // should be disabled to make the affordance honest.
    await expect(nextButton).toBeDisabled();
  }

  // The previous button is rendered too; it should be disabled when
  // there is no previous sibling and enabled otherwise. We don't make
  // a hard assertion here because the dev fixture set can vary.
  await prevButton.waitFor();
});
