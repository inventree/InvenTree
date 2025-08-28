import { test } from './baseFixtures.js';
import {
  clearTableFilters,
  navigate,
  setTableChoiceFilter
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
  await page.getByText(/1 - 25 \/ 2[2|8]/).waitFor();
  await page.getByRole('button', { name: 'Next page' }).click();
  await page.getByText(/26 - 2[7|8] \/ 2[7|8]/).waitFor();

  // Set page size to 10
  await page.getByRole('button', { name: '25' }).click();
  await page.getByRole('menuitem', { name: '10', exact: true }).click();

  await page.getByText(/1 - 10 \/ 2[7|8]/).waitFor();
  await page.getByRole('button', { name: '3' }).click();
  await page.getByText(/21 - 2[7|8] \/ 2[7|8]/).waitFor();
  await page.getByRole('button', { name: 'Previous page' }).click();
  await page.getByText(/11 - 20 \/ 2[7|8]/).waitFor();

  // Set page size back to 25
  await page.getByRole('button', { name: '10' }).click();
  await page.getByRole('menuitem', { name: '25', exact: true }).click();

  await page.getByText(/1 - 25 \/ 2[7|8]/).waitFor();
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
  await page.getByRole('menuitem', { name: 'Stocktake' }).click();
  await page.keyboard.press('Escape');

  await navigate(page, '/sales/index/salesorders');

  // Open column selector
  await page.getByLabel('table-select-columns').click();

  await page.getByRole('menuitem', { name: 'Start Date' }).click();
  await page.getByRole('menuitem', { name: 'Target Date' }).click();
  await page.getByRole('menuitem', { name: 'Reference', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Project Code' }).click();
});
