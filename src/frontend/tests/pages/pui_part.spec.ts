import { test } from '@playwright/test';

import { baseUrl } from '../defaults';
import { doQuickLogin } from '../login';

test('PUI - Pages - Part - Pricing', async ({ page }) => {
  await doQuickLogin(page);

  // Part with no history
  await page.goto(`${baseUrl}/part/82/pricing`);
  await page.getByText('1551ABK').waitFor();
  await page.getByRole('tab', { name: 'Part Pricing' }).click();
  await page.getByLabel('Part Pricing').getByText('Part Pricing').waitFor();
  await page.getByRole('button', { name: 'Pricing Overview' }).waitFor();
  await page.getByRole('button', { name: 'Pricing Overview' }).waitFor();
  await page.getByText('Last Updated').waitFor();
  await page.getByRole('button', { name: 'Purchase History' }).isDisabled();
  await page.getByRole('button', { name: 'Internal Pricing' }).isDisabled();
  await page.getByRole('button', { name: 'Supplier Pricing' }).isDisabled();

  // Part with history
  await page.goto(`${baseUrl}/part/108/pricing`);
  await page.getByText('Part: Blue Chair').waitFor();
  await page.getByRole('tab', { name: 'Part Pricing' }).click();
  await page.getByLabel('Part Pricing').getByText('Part Pricing').waitFor();
  await page.getByRole('button', { name: 'Pricing Overview' }).waitFor();
  await page.getByRole('button', { name: 'Pricing Overview' }).waitFor();
  await page.getByText('Last Updated').waitFor();
  await page.getByRole('button', { name: 'Internal Pricing' }).isDisabled();
  await page.getByRole('button', { name: 'Sale History' }).isDisabled();
  await page.getByRole('button', { name: 'Sale Pricing' }).isDisabled();
  await page.getByRole('button', { name: 'BOM Pricing' }).isEnabled();

  // Overview Graph
  let graph = page.locator('#pricing-overview-chart');
  await graph.waitFor();
  await graph.getByText('$60').waitFor();
  await graph.getByText('BOM Pricing').waitFor();
  await graph.getByText('Overall Pricing').waitFor();
  await graph.locator('path').nth(1).hover();
  await page.getByText('min_value : $50').waitFor();
  await graph.locator('path').nth(2).hover();
  await page.getByText('max_value : $52.88').waitFor();

  // BOM Pricing
  await page.getByLabel('Pricing Overview').locator('a').click();
  await page.getByRole('button', { name: 'BOM Pricing' }).isEnabled();
  await page.getByText('Bar Chart').click();
  await page.getByText('total_price_min').waitFor();
  await page.getByText('Pie Chart').click();
  await page.getByRole('button', { name: 'Quantity Not sorted' }).waitFor();
  await page.getByRole('button', { name: 'Unit Price Not sorted' }).waitFor();

  // BOM Pricing - linkjumping
  await page.getByText('Wood Screw').waitFor();
  await page.getByText('Wood Screw').click();
  await page.waitForURL('**/part/98/pricing');
});
