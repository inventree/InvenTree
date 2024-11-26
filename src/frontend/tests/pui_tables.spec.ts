import { test } from './baseFixtures.js';
import { baseUrl } from './defaults.js';
import {
  clearTableFilters,
  closeFilterDrawer,
  openFilterDrawer
} from './helpers.js';
import { doQuickLogin } from './login.js';

// Helper function to set the value of a specific table filter
const setFilter = async (page, name: string, value: string) => {
  await openFilterDrawer(page);

  await page.getByRole('button', { name: 'Add Filter' }).click();
  await page.getByPlaceholder('Select filter').click();
  await page.getByRole('option', { name: name, exact: true }).click();
  await page.getByPlaceholder('Select filter value').click();
  await page.getByRole('option', { name: value, exact: true }).click();

  await closeFilterDrawer(page);
};

test('Tables - Filters', async ({ page }) => {
  await doQuickLogin(page);

  // Head to the "build order list" page
  await page.goto(`${baseUrl}/manufacturing/index/`);

  await setFilter(page, 'Status', 'Complete');
  await setFilter(page, 'Responsible', 'allaccess');
  await setFilter(page, 'Project Code', 'PRJ-NIM');

  await clearTableFilters(page);

  // Head to the "part list" page
  await page.goto(`${baseUrl}/part/category/index/parts/`);

  await setFilter(page, 'Assembly', 'Yes');

  await clearTableFilters(page);

  // Head to the "purchase order list" page
  await page.goto(`${baseUrl}/purchasing/index/purchaseorders/`);

  await setFilter(page, 'Status', 'Complete');
  await setFilter(page, 'Responsible', 'readers');
  await setFilter(page, 'Assigned to me', 'No');
  await setFilter(page, 'Project Code', 'PRO-ZEN');

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
