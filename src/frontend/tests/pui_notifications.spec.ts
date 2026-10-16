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

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        count: notifications.length,
        next: null,
        previous: null,
        results: notifications
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
});
