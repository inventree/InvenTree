import { baseUrl } from './defaults';

/**
 * Open the filter drawer for the currently visible table
 * @param page - The page object
 */
export const openFilterDrawer = async (page) => {
  await page.getByLabel('table-select-filters').click();
};

/**
 * Close the filter drawer for the currently visible table
 * @param page - The page object
 */
export const closeFilterDrawer = async (page) => {
  await page.getByLabel('filter-drawer-close').click();
};

/**
 * Click the specified button (if it is visible)
 * @param page - The page object
 * @param name - The name of the button to click
 */
export const clickButtonIfVisible = async (page, name, timeout = 500) => {
  await page.waitForTimeout(timeout);

  if (await page.getByRole('button', { name }).isVisible()) {
    await page.getByRole('button', { name }).click();
  }
};

/**
 * Clear all filters from the currently visible table
 * @param page - The page object
 */
export const clearTableFilters = async (page) => {
  await openFilterDrawer(page);
  await clickButtonIfVisible(page, 'Clear Filters');
  await closeFilterDrawer(page);
  await page.waitForLoadState('networkidle');
};

export const setTableChoiceFilter = async (page, filter, value) => {
  await openFilterDrawer(page);

  await page.getByRole('button', { name: 'Add Filter' }).click();
  await page.getByPlaceholder('Select filter').fill(filter);
  await page.getByPlaceholder('Select filter').click();

  // Construct a regex to match the filter name exactly
  const filterRegex = new RegExp(`^${filter}$`, 'i');

  await page.getByRole('option', { name: filterRegex }).click();

  await page.getByPlaceholder('Select filter value').click();
  await page.getByRole('option', { name: value }).click();

  await closeFilterDrawer(page);
};

/**
 * Return the parent 'row' element for a given 'cell' element
 * @param cell - The cell element
 */
export const getRowFromCell = async (cell) => {
  return cell.locator('xpath=ancestor::tr').first();
};

export const clickOnRowMenu = async (cell) => {
  const row = await getRowFromCell(cell);

  await row.getByLabel(/row-action-menu-/i).click();
};

/**
 * Navigate to the provided page, and wait for loading to complete
 * @param page
 * @param url
 */
export const navigate = async (page, url: string) => {
  if (!url.startsWith(baseUrl)) {
    if (url.startsWith('/')) {
      url = url.slice(1);
    }

    url = `${baseUrl}/${url}`;
  }

  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle');
};

/**
 * CLick on the 'tab' element with the provided name
 */
export const loadTab = async (page, tabName) => {
  await page
    .getByLabel(/panel-tabs-/)
    .getByRole('tab', { name: tabName })
    .click();
  await page.waitForLoadState('networkidle');
};

/**
 * Perform a 'global search' on the provided page, for the provided query text
 */
export const globalSearch = async (page, query) => {
  await page.getByLabel('open-search').click();
  await page.getByLabel('global-search-input').clear();
  await page.getByPlaceholder('Enter search text').fill(query);
  await page.waitForTimeout(300);
  await page.waitForLoadState('networkidle');
};
