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
  await page.getByLabel('filter-drawer-close').click();
};
