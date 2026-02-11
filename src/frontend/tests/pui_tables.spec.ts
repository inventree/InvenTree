import { test } from './baseFixtures.js';
import {
  clearTableFilters,
  navigate,
  setTableChoiceFilter,
  toggleColumnSorting
} from './helpers.js';
import { doCachedLogin } from './login.js';

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
});

test('Tables - Pagination', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'manufacturing/index/buildorders',
    username: 'steven',
    password: 'wizardstaff'
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

test('Tables - Columns', async ({ browser }) => {
  // Go to the "stock list" page
  const page = await doCachedLogin(browser, {
    url: 'stock/location/index/stock-items',
    username: 'steven',
    password: 'wizardstaff'
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
    username: 'steven',
    password: 'wizardstaff'
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
