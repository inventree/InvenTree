import { expect, test } from '@playwright/test';

import { baseUrl, user } from '../defaults';
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
  await page.goto('./platform/part/108/pricing');
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
  await page.getByText('BOM PricingOverall Pricing').waitFor();
  let graph = page.locator('#pricing-overview-chart');
  await graph.waitFor();
  //await graph.screenshot({ path: 'pui_part_pricing_overview.png' });
  await graph.getByText('$45').waitFor();
  await graph.getByText('BOM Pricing').waitFor();
  await graph.getByText('Overall Pricing').waitFor();
  await graph.locator('path').nth(1).hover();
  //await graph.screenshot({ path: 'pui_part_pricing_overview_hover.png' });
  //await page.getByText('min_value:  $43*').waitFor();
});
