import { test } from './baseFixtures.js';
import {
  clearTableFilters,
  navigate,
  setTableChoiceFilter
} from './helpers.js';
import { doQuickLogin } from './login.js';

test('Tables - Filters', async ({ page }) => {
  await doQuickLogin(page);

  // Head to the "build order list" page
  await navigate(page, 'manufacturing/index/');

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

test('Tables - Columns', async ({ page }) => {
  await doQuickLogin(page);

  // Go to the "stock list" page
  await navigate(page, 'stock/location/index/stock-items');

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

  await page.waitForTimeout(1000);
});
