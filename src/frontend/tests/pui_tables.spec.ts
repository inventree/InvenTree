import { test } from './baseFixtures.js';
import { baseUrl } from './defaults.js';
import { clearTableFilters, setTableChoiceFilter } from './helpers.js';
import { doQuickLogin } from './login.js';

test('Tables - Filters', async ({ page }) => {
  await doQuickLogin(page);

  // Head to the "build order list" page
  await page.goto(`${baseUrl}/manufacturing/index/`);

  await clearTableFilters(page);

  await setTableChoiceFilter(page, 'Status', 'Complete');
  await setTableChoiceFilter(page, 'Responsible', 'allaccess');
  await setTableChoiceFilter(page, 'Project Code', 'PRJ-NIM');

  await clearTableFilters(page);

  // Head to the "part list" page
  await page.goto(`${baseUrl}/part/category/index/parts/`);

  await setTableChoiceFilter(page, 'Assembly', 'Yes');

  await clearTableFilters(page);

  // Head to the "purchase order list" page
  await page.goto(`${baseUrl}/purchasing/index/purchaseorders/`);

  await clearTableFilters(page);

  await setTableChoiceFilter(page, 'Status', 'Complete');
  await setTableChoiceFilter(page, 'Responsible', 'readers');
  await setTableChoiceFilter(page, 'Assigned to me', 'No');
  await setTableChoiceFilter(page, 'Project Code', 'PRO-ZEN');

  await clearTableFilters(page);
});

test('Tables - Columns', async ({ page }) => {
  await doQuickLogin(page);

  // Go to the "stock list" page
  await page.goto(`${baseUrl}/stock/location/index/stock-items`);

  // Open column selector
  await page.getByLabel('table-select-columns').click();

  // De-select some items
  await page.getByRole('menuitem', { name: 'Description' }).click();
  await page.getByRole('menuitem', { name: 'Stocktake' }).click();
});
