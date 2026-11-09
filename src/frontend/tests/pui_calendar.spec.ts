/**
 * Tests for the order "calendar" views.
 *
 * The demo dataset does not contain any orders in the current month,
 * so each test creates an order (via the API) which is visible in the
 * default calendar view. This allows the event rendering, tooltip,
 * click and drag handlers to be exercised.
 */

import type { Page } from '@playwright/test';
import { createApi } from './api.js';
import { expect, generateUUID, test } from './baseFixtures.js';
import { loadTab, showCalendarView, showTableView } from './helpers.js';
import { doCachedLogin } from './login.js';

// Return a YYYY-MM-DD date string for a given day in the current month
const dateInMonth = (day: number): string => {
  const now = new Date();
  const d = new Date(now.getFullYear(), now.getMonth(), day);
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}-${mm}-${dd}`;
};

const firstResult = async (api, url: string, params: any) => {
  const response = await api.get(url, { params: { limit: 1, ...params } });
  expect(response.status()).toBe(200);
  const data = await response.json();
  return (data.results ?? data)[0];
};

/**
 * Exercise the common calendar functionality for an order which
 * is known to be displayed in the current month
 */
const exerciseCalendar = async (page: Page, description: string) => {
  await showCalendarView(page);

  // Search for the order within the calendar
  await page.getByLabel('table-search-input').fill(description);
  await page.waitForTimeout(600);
  await page.waitForLoadState('networkidle');

  const event = page.getByText(description, { exact: true }).first();
  await event.waitFor();

  // Hover over the event to display the tooltip
  await event.hover();
  await page.getByText('Target Date').first().waitFor();

  // Drag the event to a different day, triggering an update to the order
  const target = page.locator('td.fc-day').filter({ hasText: /^15$/ }).first();

  if (await target.isVisible()) {
    await event.dragTo(target);
    await page.waitForLoadState('networkidle');
  }

  // Toggle the calendar filters
  await page.getByLabel('calendar-select-filters').click();
  await page.getByText('Calendar Filters').first().waitFor();
  await page.keyboard.press('Escape');

  // Refresh the calendar
  await page.getByLabel('calendar-refresh').click();
  await page.waitForLoadState('networkidle');

  // Open the export modal
  await page.getByLabel('calendar-export-data').click();
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Navigate months
  await page.getByLabel('action-button-next-month').click();
  await page.getByLabel('action-button-previous-month').click();

  // Click the event to open the preview drawer (or navigate to the order)
  const url = page.url();
  await page.getByText(description, { exact: true }).first().click();
  await page.waitForLoadState('networkidle');
  await page.keyboard.press('Escape');

  if (page.url() != url) {
    await page.goBack();
  }

  // Restore the table view
  await showTableView(page);
};

test('Calendar - Purchase Orders', async ({ browser }) => {
  const api = await createApi({});
  const description = `pw-cal-po-${generateUUID().slice(0, 8)}`;
  const supplier = await firstResult(api, 'company/', { is_supplier: true });

  const response = await api.post('order/po/', {
    data: {
      supplier: supplier.pk,
      description: description,
      start_date: dateInMonth(8),
      target_date: dateInMonth(10)
    }
  });
  expect(response.status()).toBe(201);
  const order = await response.json();

  const page = await doCachedLogin(browser, { url: 'purchasing/index/' });
  await loadTab(page, 'Purchase Orders');
  await exerciseCalendar(page, description);

  // Cleanup
  await api.post(`order/po/${order.pk}/cancel/`, {});
});

test('Calendar - Sales Orders', async ({ browser }) => {
  const api = await createApi({});
  const description = `pw-cal-so-${generateUUID().slice(0, 8)}`;
  const customer = await firstResult(api, 'company/', { is_customer: true });

  const response = await api.post('order/so/', {
    data: {
      customer: customer.pk,
      description: description,
      start_date: dateInMonth(8),
      target_date: dateInMonth(10)
    }
  });
  expect(response.status()).toBe(201);
  const order = await response.json();

  const page = await doCachedLogin(browser, { url: 'sales/index/' });
  await loadTab(page, 'Sales Orders');
  await exerciseCalendar(page, description);

  await api.post(`order/so/${order.pk}/cancel/`, {});
});

test('Calendar - Return Orders', async ({ browser }) => {
  const api = await createApi({});
  const description = `pw-cal-ro-${generateUUID().slice(0, 8)}`;
  const customer = await firstResult(api, 'company/', { is_customer: true });

  const response = await api.post('order/ro/', {
    data: {
      customer: customer.pk,
      description: description,
      start_date: dateInMonth(8),
      target_date: dateInMonth(10)
    }
  });
  expect(response.status()).toBe(201);
  const order = await response.json();

  const page = await doCachedLogin(browser, { url: 'sales/index/' });
  await loadTab(page, 'Return Orders');
  await exerciseCalendar(page, description);

  await api.post(`order/ro/${order.pk}/cancel/`, {});
});

test('Calendar - Build Orders', async ({ browser }) => {
  const api = await createApi({});
  const title = `pw-cal-bo-${generateUUID().slice(0, 8)}`;
  const part = await firstResult(api, 'part/', {
    assembly: true,
    active: true
  });

  const response = await api.post('build/', {
    data: {
      part: part.pk,
      quantity: 1,
      title: title,
      start_date: dateInMonth(8),
      target_date: dateInMonth(10)
    }
  });
  expect(response.status()).toBe(201);
  const build = await response.json();

  const page = await doCachedLogin(browser, { url: 'manufacturing/index/' });
  await loadTab(page, 'Build Orders');
  await exerciseCalendar(page, title);

  await api.post(`build/${build.pk}/cancel/`, {});
});
