import { expect } from '@playwright/test';
import { test } from './baseFixtures.js';
import { stevenuser } from './defaults.js';
import {
  clearTableFilters,
  navigate,
  openFilterDrawer,
  setTableChoiceFilter,
  toggleColumnSorting
} from './helpers.js';
import { doCachedLogin } from './login.js';

// Test filtering by "quick filter" actions (against table columns)
test('Tables - Quick Filters', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'part/category/index/parts/'
  });

  await clearTableFilters(page);

  await page
    .getByRole('button', { name: 'Part Not sorted' })
    .getByRole('button')
    .first()
    .click();
  await page.getByRole('combobox', { name: 'choice-filter-active' }).click();
  await page.getByRole('option', { name: 'Yes' }).click();

  await page
    .getByRole('button', { name: 'Part Not sorted' })
    .getByRole('button')
    .first()
    .click();
  await page.getByRole('combobox', { name: 'choice-filter-locked' }).click();
  await page.getByRole('option', { name: 'No' }).click();

  await page
    .getByRole('button', { name: 'IPN Not sorted' })
    .getByRole('button')
    .first()
    .click();
  await page.getByRole('combobox', { name: 'choice-filter-has_ipn' }).click();
  await page.getByRole('option', { name: 'Yes' }).click();

  await page.getByRole('cell', { name: 'ENCAB' }).first().waitFor();
});

test('Tables - Filters', async ({ browser }) => {
  // Head to the "build order list" page
  const page = await doCachedLogin(browser, { url: 'manufacturing/index/' });

  await clearTableFilters(page);

  await setTableChoiceFilter(page, 'Status', 'Complete');
  await setTableChoiceFilter(page, 'Responsible', 'allaccess');
  await setTableChoiceFilter(page, 'Project Code', 'PRJ-NIM');

  await clearTableFilters(page);

  // Head to the "part list" page
  await navigate(page, 'part/category/index/parts/');

  await setTableChoiceFilter(page, 'Assembly', 'Yes');

  await clearTableFilters(page);

  // Head to the "purchase order list" page
  await navigate(page, 'purchasing/index/purchaseorders/');

  await clearTableFilters(page);

  await setTableChoiceFilter(page, 'Status', 'Complete');
  await setTableChoiceFilter(page, 'Responsible', 'readers');
  await setTableChoiceFilter(page, 'Assigned to me', 'No');
  await setTableChoiceFilter(page, 'Project Code', 'PRO-ZEN');
  await setTableChoiceFilter(page, 'Has Start Date', 'Yes');

  await clearTableFilters(page);

  // Next, let's create a "custom filter group" and apply it
  await openFilterDrawer(page);
  await page.getByRole('button', { name: 'Add Filter' }).click();
  await page.getByRole('combobox', { name: 'Filter' }).click();
  await page.getByRole('option', { name: 'Outstanding' }).click();

  await page
    .getByRole('combobox', { name: 'choice-filter-outstanding' })
    .click();
  await page.getByRole('option', { name: 'Yes' }).click();

  // Save the filter group
  await page.getByRole('button', { name: 'Save Filters' }).click();
  await page.getByRole('textbox', { name: 'filter-group-name' }).fill('custom');
  await page
    .getByRole('button', { name: 'save-filter-set', exact: true })
    .click();

  // Clear filters, and then restore from saved group
  await page.getByRole('button', { name: 'Clear Filters' }).click();
  await page.getByRole('button', { name: 'load-filter-group-custom' }).click();
  await page.getByText('Show outstanding items').first().waitFor();

  // Remove the filter group
  await page
    .getByRole('button', { name: 'delete-filter-group-custom' })
    .click();
});

test('Tables - Pagination', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'manufacturing/index/buildorders',
    user: stevenuser
  });

  await clearTableFilters(page);

  // Expected pagination size is 25
  // Note: Due to other tests, there may be more than 25 items in the list
  await page.getByText(/1 - 25 \/ \d+/).waitFor();
  await page.getByRole('button', { name: 'Next page' }).click();
  await page.getByText(/26 - \d+ \/ \d+/).waitFor();

  // Set page size to 10
  await page.getByRole('button', { name: '25' }).click();
  await page.getByRole('menuitem', { name: '10', exact: true }).click();

  await page.getByText(/1 - 10 \/ \d+/).waitFor();
  await page.getByRole('button', { name: '3' }).click();
  await page.getByText(/21 - \d+ \/ \d+/).waitFor();
  await page.getByRole('button', { name: 'Previous page' }).click();
  await page.getByText(/11 - 20 \/ \d+/).waitFor();

  // Set page size back to 25
  await page.getByRole('button', { name: '10' }).click();
  await page.getByRole('menuitem', { name: '25', exact: true }).click();

  await page.getByText(/1 - 25 \/ \d+/).waitFor();
});

test('Tables - Navigation query parameters', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'part/category/index/parts/'
  });

  await clearTableFilters(page);

  const navigationParams = new URLSearchParams({
    _na: 'p',
    _nq: 'search=530470',
    _ni: '0',
    _np: '69',
    _nf: 'pk'
  });

  const waitForPartList = () =>
    page.waitForResponse((response) => {
      const url = new URL(response.url());

      return (
        response.request().method() === 'GET' &&
        url.pathname === '/api/part/' &&
        url.searchParams.has('limit')
      );
    });

  const navigationRequest = waitForPartList();
  await navigate(
    page,
    `part/category/index/parts/?${navigationParams.toString()}`
  );

  const navigationRequestUrl = new URL((await navigationRequest).url());

  for (const key of navigationParams.keys()) {
    expect(navigationRequestUrl.searchParams.has(key)).toBe(false);
  }

  await expect(page.getByText('Custom table filters are active')).toHaveCount(
    0
  );
  await expect(page.getByLabel('table-select-filters')).toBeEnabled();

  await setTableChoiceFilter(page, 'Assembly', 'Yes');

  for (const [key, value] of navigationParams) {
    expect(new URL(page.url()).searchParams.get(key)).toBe(value);
  }

  await clearTableFilters(page);

  for (const [key, value] of navigationParams) {
    expect(new URL(page.url()).searchParams.get(key)).toBe(value);
  }

  const searchParams = new URLSearchParams(navigationParams);
  searchParams.set('search', '530470');

  const searchRequest = waitForPartList();
  await navigate(page, `part/category/index/parts/?${searchParams.toString()}`);

  const searchRequestUrl = new URL((await searchRequest).url());
  expect(searchRequestUrl.searchParams.get('search')).toBe('530470');

  for (const key of navigationParams.keys()) {
    expect(searchRequestUrl.searchParams.has(key)).toBe(false);
  }

  await expect(page.getByRole('cell', { name: '530470210' })).toBeVisible();

  const queryFilterAlert = page
    .getByRole('alert')
    .filter({ hasText: 'Custom table filters are active' });
  await expect(queryFilterAlert).toBeVisible();
  await expect(page.getByLabel('table-select-filters')).toBeDisabled();

  await queryFilterAlert.getByRole('button').click();
  await expect(queryFilterAlert).toBeHidden();
  await expect
    .poll(() => new URL(page.url()).searchParams.has('search'))
    .toBe(false);

  for (const [key, value] of navigationParams) {
    expect(new URL(page.url()).searchParams.get(key)).toBe(value);
  }

  await expect(page.getByLabel('table-select-filters')).toBeEnabled();
});

test('Tables - Detail navigation', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'part/category/index/parts/?search=530470'
  });

  const firstRow = page.locator('tbody tr').first();
  await firstRow.waitFor();
  await firstRow.locator('td').nth(1).click();
  await page.waitForURL(/\/web\/part\/\d+(?:\/.*)?$/);

  const position = page.getByText(/^\d+ of \d+$/).first();
  await expect(position).toHaveText('1 of 2');

  const breadcrumbBar = page.getByTestId('breadcrumb-list');
  const detailNavigation = breadcrumbBar.getByTestId('detail-navigation');
  await expect(detailNavigation).toBeVisible();

  const previous = page.getByLabel('Previous item', { exact: true });
  await expect(previous).toBeVisible();
  await expect(previous.locator('svg')).toBeVisible();
  await expect(previous).toHaveAttribute('data-disabled', 'true');
  await expect(previous).not.toHaveAttribute('href');

  const next = page.getByLabel('Next item', { exact: true });
  await expect(next).toBeVisible();
  await expect(next.locator('svg')).toBeVisible();
  await expect(next).not.toHaveAttribute('data-disabled');

  const nextHref = await next.getAttribute('href');
  expect(nextHref).toContain('_na=p');
  expect(nextHref).toContain('_ni=1');
  expect(nextHref).toContain('_np=');
  expect(nextHref).not.toContain('_nav_');
  expect(nextHref).not.toContain('_nf=');

  const initialBreadcrumbHeight = (await breadcrumbBar.boundingBox())?.height;

  await next.click();
  await expect(position).toHaveText('2 of 2');

  const nextBreadcrumbHeight = (await breadcrumbBar.boundingBox())?.height;
  expect(initialBreadcrumbHeight).toBeDefined();
  expect(nextBreadcrumbHeight).toBeDefined();
  expect(
    Math.abs((nextBreadcrumbHeight ?? 0) - (initialBreadcrumbHeight ?? 0))
  ).toBeLessThanOrEqual(1);

  await expect(previous).toBeVisible();
  await expect(previous.locator('svg')).toBeVisible();
  await expect(previous).not.toHaveAttribute('data-disabled');
  await expect(previous).toHaveAttribute('href');

  await expect(next).toBeVisible();
  await expect(next.locator('svg')).toBeVisible();
  await expect(next).toHaveAttribute('data-disabled', 'true');
  await expect(next).not.toHaveAttribute('href');

  await previous.click();
  await expect(position).toHaveText('1 of 2');
  await expect(previous).toHaveAttribute('data-disabled', 'true');
  await expect(previous).not.toHaveAttribute('href');
  await expect(next).not.toHaveAttribute('data-disabled');
  await expect(next).toHaveAttribute('href');
});

test('Tables - Columns', async ({ browser }) => {
  // Go to the "stock list" page
  const page = await doCachedLogin(browser, {
    url: 'stock/location/index/stock-items',
    user: stevenuser
  });

  // Open column selector
  await page.getByLabel('table-select-columns').click();

  // De-select some items
  await page.getByRole('menuitem', { name: 'Description' }).click();
  await page.getByRole('menuitem', { name: 'Batch Code' }).click();

  await page.keyboard.press('Escape');

  await navigate(page, '/sales/index/salesorders');

  // Open column selector
  await page.getByLabel('table-select-columns').click();

  await page.getByRole('menuitem', { name: 'Start Date' }).click();
  await page.getByRole('menuitem', { name: 'Target Date' }).click();
  await page.getByRole('menuitem', { name: 'Reference', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Project Code' }).click();
});

test('Tables - Sorting', async ({ browser }) => {
  // Go to the "stock list" page
  const page = await doCachedLogin(browser, {
    url: 'stock/location/index/stock-items',
    user: stevenuser
  });

  // Stock table sorting
  await toggleColumnSorting(page, 'Part');
  await toggleColumnSorting(page, 'IPN');
  await toggleColumnSorting(page, 'Stock');
  await toggleColumnSorting(page, 'Status');

  // Purchase order sorting
  await navigate(page, '/web/purchasing/index/purchaseorders');
  await toggleColumnSorting(page, 'Reference');
  await toggleColumnSorting(page, 'Supplier');
  await toggleColumnSorting(page, 'Order Status');
  await toggleColumnSorting(page, 'Line Items');
});
