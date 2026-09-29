import { expect, test } from './baseFixtures.js';
import { adminuser } from './defaults.js';
import { loadTab } from './helpers.js';
import { doCachedLogin } from './login.js';

for (const outcome of ['warnings', 'error', 'success'] as const) {
  test(`Printing - Result ${outcome}`, async ({ browser }) => {
    const page = await doCachedLogin(browser, {
      user: adminuser,
      url: 'stock/location/index/'
    });
    const warning = '<img src=x onerror="alert(1)"> Check serial number';
    const warnings = [
      warning,
      'Long warning\n'.repeat(30),
      ...Array.from({ length: 5 }, (_, index) => `Warning ${index + 3}`)
    ];
    let finished = false;
    let polls = 0;
    let outputOpened = false;

    await page.route('**/api/label/print/', (route) => {
      if (route.request().method() !== 'POST') return route.continue();
      return route.fulfill({ json: { pk: 987654, complete: false } });
    });
    await page.route('**/api/data-output/987654/**', (route) => {
      polls += 1;
      return route.fulfill({
        json: {
          pk: 987654,
          complete: finished,
          progress: 1,
          total: 2,
          warnings: outcome === 'success' ? undefined : warnings,
          errors:
            finished && outcome === 'error'
              ? { error: 'Printer failed' }
              : null,
          output:
            finished && outcome !== 'error' ? '/media/warning-test.html' : null
        }
      });
    });
    await page.context().route('**/media/warning-test.html', (route) => {
      outputOpened = true;
      return route.fulfill({
        contentType: 'text/html',
        body: 'Rendered output'
      });
    });

    await loadTab(page, 'Stock Items');
    await page.getByLabel('Select record 1', { exact: true }).click();
    await page
      .getByLabel('Stock Items')
      .getByLabel('action-menu-printing-actions')
      .click();
    await page.getByLabel('action-menu-printing-actions-print-labels').click();
    await page.getByLabel('related-field-template').click();
    await page
      .getByRole('option', { name: 'InvenTree Stock Item Label' })
      .click();
    await page.getByLabel('related-field-plugin').click();
    await page.getByRole('option', { name: 'InvenTreeLabel provides' }).click();
    await page.getByRole('button', { name: 'Print', exact: true }).click();

    await expect.poll(() => polls).toBeGreaterThan(1);
    const pendingNotice = page.locator('.mantine-Notification-root').filter({
      has: page.getByRole('progressbar')
    });
    await expect(pendingNotice).toBeVisible();
    await expect(
      pendingNotice.locator('.mantine-Notification-loader')
    ).toBeVisible();
    if (outcome !== 'success') {
      await expect(
        pendingNotice.getByText(warning, { exact: true })
      ).toBeVisible();
      await expect(pendingNotice.locator('img')).toHaveCount(0);
      await expect(pendingNotice.getByRole('listitem')).toHaveCount(5);
      await expect(pendingNotice.getByText('2 more warnings')).toBeVisible();
      await expect(pendingNotice.getByText('Warning 6')).toHaveCount(0);
      expect(
        await pendingNotice
          .getByRole('list')
          .evaluate((list) => list.scrollHeight > list.clientHeight)
      ).toBe(true);
    } else {
      await expect(pendingNotice.getByRole('list')).toHaveCount(0);
    }
    const pendingPolls = polls;
    await expect.poll(() => polls).toBeGreaterThan(pendingPolls);
    expect(outputOpened).toBe(false);
    finished = true;

    if (outcome === 'warnings') {
      const notice = page.locator('.mantine-Notification-root').filter({
        hasText: 'Process completed with warnings'
      });
      await expect(notice.getByText(warning, { exact: true })).toBeVisible();
      await expect(notice.locator('img')).toHaveCount(0);
      await expect(notice.getByRole('listitem')).toHaveCount(5);
      await expect(notice.getByText('2 more warnings')).toBeVisible();
      await expect(
        notice.getByRole('link', { name: 'Open output' })
      ).toHaveAttribute('href', /\/media\/warning-test\.html$/);
      await expect.poll(() => outputOpened).toBe(true);
      // Successful results normally disappear after 2.5 seconds.
      await page.waitForTimeout(3000);
      await expect(notice).toBeVisible();
      await notice.getByRole('button').click();
      await expect(notice).toHaveCount(0);
    } else if (outcome === 'error') {
      await expect(
        page.getByText('Printer failed', { exact: true })
      ).toBeVisible();
      await expect(page.getByText(warning, { exact: true })).toHaveCount(0);
      expect(outputOpened).toBe(false);
    } else {
      const notice = page.locator('.mantine-Notification-root').filter({
        hasText: 'Process completed successfully'
      });
      await expect(notice).toBeVisible();
      await expect.poll(() => outputOpened).toBe(true);
      await expect(notice).toBeHidden();
    }

    await page.context().close();
  });
}
