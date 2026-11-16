/**
 * Tests for the "parametric" table view (part parameters)
 */

import type { Page } from '@playwright/test';
import { test } from '../baseFixtures.js';
import {
  clearTableFilters,
  clickOnParamFilter,
  showParametricView,
  showTableView
} from '../helpers.js';
import { doCachedLogin } from '../login.js';

// Click on the parameter cell for the given column (in the specified row)
const clickParameterCell = async (page: Page, column: string, row = 0) => {
  const headers = page.locator('table thead th');
  const count = await headers.count();

  for (let idx = 0; idx < count; idx++) {
    const text = (await headers.nth(idx).innerText()).trim();
    if (text.startsWith(column)) {
      await page
        .locator('table tbody tr')
        .nth(row)
        .locator('td')
        .nth(idx)
        .click();
      return;
    }
  }

  throw new Error(`Column ${column} not found`);
};

// Find (and click) the first empty cell in any of the provided columns
const clickEmptyParameterCell = async (
  page: Page,
  columns: string[]
): Promise<boolean> => {
  const headers = page.locator('table thead th');
  const count = await headers.count();
  const rows = page.locator('table tbody tr');
  const rowCount = await rows.count();

  for (let idx = 0; idx < count; idx++) {
    const text = (await headers.nth(idx).innerText()).trim();

    if (!columns.some((col) => text.startsWith(col))) continue;

    for (let row = 0; row < rowCount; row++) {
      const cell = rows.nth(row).locator('td').nth(idx);
      if ((await cell.innerText()).trim() === '') {
        await cell.click();
        return true;
      }
    }
  }

  return false;
};

test('Parametric - Filters and Editing', async ({ browser }) => {
  // "Resistors" category - parts with numeric parameters
  const page = await doCachedLogin(browser, {
    url: 'part/category/5/parts'
  });

  await showParametricView(page);
  await clearTableFilters(page);

  // Numeric filter, with a custom operator
  await clickOnParamFilter(page, 'Resistance [ohms]');
  await page
    .getByRole('combobox', { name: 'filter-Resistance-operator' })
    .last()
    .click();
  await page.getByRole('option', { name: '>', exact: true }).click();
  await page.getByLabel('filter-Resistance', { exact: true }).last().fill('1k');
  await page
    .getByLabel('filter-Resistance', { exact: true })
    .last()
    .press('Enter');
  await page.waitForLoadState('networkidle');

  // Add a second filter on the same column
  await clickOnParamFilter(page, 'Resistance [ohms]');
  await page
    .getByRole('combobox', { name: 'filter-Resistance-operator' })
    .last()
    .click();
  await page.getByRole('option', { name: '<', exact: true }).click();
  await page
    .getByLabel('filter-Resistance', { exact: true })
    .last()
    .fill('100k');
  await page
    .getByLabel('filter-Resistance', { exact: true })
    .last()
    .press('Enter');
  await page.waitForLoadState('networkidle');

  // Clear the filter
  await clickOnParamFilter(page, 'Resistance [ohms]');
  await page.getByLabel('clear-filter-Resistance').first().click();
  await page.waitForLoadState('networkidle');
  await page.keyboard.press('Escape');

  // Edit an existing parameter value
  await clickParameterCell(page, 'Resistance');
  await page.getByRole('button', { name: 'Submit' }).waitFor();
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Add a parameter value which does not yet exist (find an empty cell)
  if (await clickEmptyParameterCell(page, ['Power', 'Tolerance', 'Package'])) {
    await page.getByRole('button', { name: 'Cancel' }).click();
  }

  await showTableView(page);
});
