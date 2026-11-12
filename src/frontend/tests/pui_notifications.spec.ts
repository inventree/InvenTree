import { expect, test } from './baseFixtures.js';
import { doLogin } from './login.js';

const notifications = [
  {
    pk: 1,
    target: {
      model_type: 'pluginconfig',
      model_id: 1,
      link: 'https://example.com/path'
    },
    source: null,
    user: 1,
    category: 'test_external',
    name: 'External Notification',
    message: 'External notification link',
    creation: '2026-09-12 12:00',
    age: 1,
    age_human: 'a moment ago',
    read: false
  },
  {
    pk: 2,
    target: {
      model_type: 'pluginconfig',
      model_id: 1,
      link: '/settings/admin/'
    },
    source: null,
    user: 1,
    category: 'test_internal',
    name: 'Internal Notification',
    message: 'Internal notification link',
    creation: '2026-09-12 12:00',
    age: 1,
    age_human: 'a moment ago',
    read: false
  },
  {
    pk: 3,
    target: {
      model_type: 'pluginconfig',
      model_id: 1,
      link: '/web/settings/admin/'
    },
    source: null,
    user: 1,
    category: 'test_base',
    name: 'Base Notification',
    message: 'Notification link with base path',
    creation: '2026-09-12 12:00',
    age: 1,
    age_human: 'a moment ago',
    read: false
  }
];

test('Notifications - link targets', async ({ page }) => {
  await page.route('**/api/notifications/**', async (route) => {
    if (route.request().method() !== 'GET') {
      await route.continue();
      return;
    }

    // Absolute link to a page on the same server (as provided by the backend)
    const origin = new URL(page.url()).origin;

    const results = [
      ...notifications,
      {
        ...notifications[1],
        pk: 4,
        target: {
          ...notifications[1].target,
          link: `${origin}/web/part/category/index/`
        },
        category: 'test_absolute',
        name: 'Absolute Notification',
        message: 'Absolute notification link'
      }
    ];

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        count: results.length,
        next: null,
        previous: null,
        results: results
      })
    });
  });

  await doLogin(page);

  await page.getByRole('button', { name: 'open-notifications' }).click();

  await expect(
    page.getByRole('link', { name: 'External Notification' })
  ).toHaveAttribute('href', 'https://example.com/path');

  await expect(
    page.getByRole('link', { name: 'Internal Notification' })
  ).toHaveAttribute('href', '/web/settings/admin/');

  await expect(
    page.getByRole('link', { name: 'Base Notification' })
  ).toHaveAttribute('href', '/web/settings/admin/');

  await expect(
    page.getByRole('link', { name: 'Absolute Notification' })
  ).toHaveAttribute('href', '/web/part/category/index/');

  // Clicking an internal link should route within the app (no page reload)
  await page.evaluate(() => {
    (window as any).__noReload = true;
  });

  await page.getByRole('link', { name: 'Absolute Notification' }).click();
  await page.waitForURL('**/web/part/category/index/**');

  expect(await page.evaluate(() => (window as any).__noReload)).toBe(true);
});
