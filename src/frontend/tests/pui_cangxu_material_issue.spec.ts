import { expect } from '@playwright/test';
import { test } from './baseFixtures.js';
import { allaccessuser } from './defaults.js';
import { doCachedLogin } from './login.js';

test('Cangxu - Issue and return consumable material', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    user: allaccessuser,
    url: 'cangxu/'
  });
  const issueRequests: unknown[] = [];
  const returnRequests: unknown[] = [];
  const issue = {
    id: 31,
    build_line: 17,
    build_reference: 'CX-BUILD-001',
    part_name: 'GPU power cable',
    part_code: 'CX-CABLE-001',
    stock_item: 42,
    quantity: '3.00000',
    returned_quantity: '0.00000',
    remaining_quantity: '3.00000'
  };

  await page.route('**/api/build/line/**', async (route) => {
    await route.fulfill({
      json: {
        count: 1,
        results: [
          {
            pk: 17,
            build: 7,
            consumable: true,
            trackable: false,
            quantity: '5.00000',
            consumed: '0.00000',
            part_detail: { name: 'GPU power cable', IPN: 'CX-CABLE-001' }
          }
        ]
      }
    });
  });
  await page.route('**/api/build/**', async (route) => {
    if (route.request().url().includes('/build/line/')) {
      await route.fallback();
      return;
    }
    await route.fulfill({
      json: {
        count: 1,
        results: [
          {
            pk: 7,
            reference: 'CX-BUILD-001',
            title: 'Synthetic GPU server build',
            part_detail: { name: 'Synthetic GPU server', IPN: 'CX-SERVER-001' },
            status: 10,
            status_text: 'Pending',
            quantity: '1.00000',
            completed: '0.00000'
          }
        ]
      }
    });
  });
  await page.route('**/api/stock/location/**', async (route) => {
    await route.fulfill({
      json: {
        count: 1,
        results: [
          {
            pk: 9,
            name: 'Synthetic production stock',
            external: false,
            structural: false
          }
        ]
      }
    });
  });
  await page.route('**/api/stock/**', async (route) => {
    if (route.request().url().includes('/stock/location/')) {
      await route.fallback();
      return;
    }
    await route.fulfill({
      json: {
        count: 1,
        results: [
          {
            pk: 42,
            part_detail: { name: 'GPU power cable', IPN: 'CX-CABLE-001' },
            quantity: '8.00000',
            location: 9,
            location_detail: { name: 'Synthetic production stock' },
            status: 10,
            in_stock: true,
            allocated: false
          }
        ]
      }
    });
  });
  await page.route('**/api/cangxu/material-issues/**', async (route) => {
    const request = route.request();
    if (request.method() === 'GET') {
      await route.fulfill({
        json: {
          count: issue.remaining_quantity === '0.00000' ? 0 : 1,
          results: issue.remaining_quantity === '0.00000' ? [] : [issue]
        }
      });
    } else if (
      request.method() === 'POST' &&
      request.url().includes('/return_stock/')
    ) {
      returnRequests.push(request.postDataJSON());
      issue.returned_quantity = '1.00000';
      issue.remaining_quantity = '2.00000';
      await route.fulfill({ status: 201, json: issue });
    } else if (request.method() === 'POST') {
      issueRequests.push(request.postDataJSON());
      issue.remaining_quantity = '3.00000';
      await route.fulfill({ status: 201, json: issue });
    } else {
      await route.fallback();
    }
  });

  await expect(page.getByText('Consumable materials')).toBeVisible();
  await page.getByRole('combobox', { name: 'Build order' }).click();
  await page.getByRole('option', { name: /CX-BUILD-001/ }).click();
  await page.getByRole('combobox', { name: 'Consumable BOM line' }).click();
  await page.getByRole('option', { name: /CX-CABLE-001/ }).click();
  await page
    .getByRole('combobox', { name: 'Available stock' })
    .fill('GPU power');
  await page.getByRole('option', { name: /CX-CABLE-001/ }).click();
  await page.getByLabel('Issue quantity').fill('3');
  await page.getByRole('button', { name: 'Confirm issue' }).click();
  await expect(page.getByText('Material issued')).toBeVisible();
  expect(issueRequests).toHaveLength(1);
  expect(issueRequests[0]).toMatchObject({
    build_line: 17,
    stock_item: 42,
    quantity: '3'
  });

  await page.getByRole('tab', { name: 'Return unused material' }).click();
  await page.getByRole('combobox', { name: 'Original material issue' }).click();
  await page
    .getByRole('option', { name: /CX-BUILD-001.*GPU power cable/ })
    .click();
  await page.getByLabel('Return quantity').fill('1');
  await page.getByRole('combobox', { name: 'Return to location' }).click();
  await page
    .getByRole('option', { name: 'Synthetic production stock' })
    .click();
  await page.getByRole('button', { name: 'Confirm return' }).click();
  await expect(page.getByText('Material returned')).toBeVisible();
  expect(returnRequests).toHaveLength(1);
  expect(returnRequests[0]).toMatchObject({ quantity: '1', location: 9 });
});
