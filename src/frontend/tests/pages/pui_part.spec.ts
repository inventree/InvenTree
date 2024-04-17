import { test } from '@playwright/test';

import { baseUrl } from '../defaults';
import { doQuickLogin } from '../login';

test('PUI - Pages - Part - Pricing (Nothing, BOM)', async ({ page }) => {
  await doQuickLogin(page);

  // Part with no history
  await page.goto(`${baseUrl}/part/82/pricing`);
  await page.getByText('1551ABK').waitFor();
  await page.getByRole('tab', { name: 'Part Pricing' }).click();
  await page.getByLabel('Part Pricing').getByText('Part Pricing').waitFor();
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

  // BOM Pricing
  await page.getByRole('button', { name: 'BOM Pricing' }).click();
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

test('PUI - Pages - Part - Pricing (Supplier)', async ({ page }) => {
  await doQuickLogin(page);

  // Part
  await page.goto(`${baseUrl}/part/55/pricing`);
  await page.getByText('Part: C_100nF_0603').waitFor();
  await page.getByRole('tab', { name: 'Part Pricing' }).click();
  await page.getByLabel('Part Pricing').getByText('Part Pricing').waitFor();
  await page.getByRole('button', { name: 'Pricing Overview' }).waitFor();
  await page.getByText('Last Updated').waitFor();
  await page.getByRole('button', { name: 'Purchase History' }).isEnabled();
  await page.getByRole('button', { name: 'Internal Pricing' }).isDisabled();
  await page.getByRole('button', { name: 'Supplier Pricing' }).isEnabled();

  // Supplier Pricing
  await page.getByRole('button', { name: 'Supplier Pricing' }).click();
  await page.waitForTimeout(500);
  await page.getByRole('button', { name: 'SKU Not sorted' }).waitFor();

  // Supplier Pricing - linkjumping
  let target = page.getByText('ARR-26041-LPC').first();
  await target.waitFor();
  await target.click();
  await page.waitForURL('**/purchasing/supplier-part/697/');
});

test('PUI - Pages - Part - Pricing (Variant)', async ({ page }) => {
  await doQuickLogin(page);

  // Part
  await page.goto(`${baseUrl}/part/106/pricing`);
  await page.getByText('Part: Chair').waitFor();
  await page.getByRole('tab', { name: 'Part Pricing' }).click();
  await page.getByLabel('Part Pricing').getByText('Part Pricing').waitFor();
  await page.getByRole('button', { name: 'Pricing Overview' }).waitFor();
  await page.getByText('Last Updated').waitFor();
  await page.getByRole('button', { name: 'Internal Pricing' }).isDisabled();
  await page.getByRole('button', { name: 'BOM Pricing' }).isEnabled();
  await page.getByRole('button', { name: 'Variant Pricing' }).isEnabled();
  await page.getByRole('button', { name: 'Sale Pricing' }).isDisabled();
  await page.getByRole('button', { name: 'Sale History' }).isDisabled();

  // Variant Pricing
  await page.getByRole('button', { name: 'Variant Pricing' }).click();
  await page.waitForTimeout(500);
  await page.getByRole('button', { name: 'Variant Part Not sorted' }).click();

  // Variant Pricing - linkjumping
  let target = page.getByText('Green Chair').first();
  await target.waitFor();
  await target.click();
  await page.waitForURL('**/part/109/pricing');
});

test('PUI - Pages - Part - Pricing (Internal)', async ({ page }) => {
  await doQuickLogin(page);

  // Part
  await page.goto(`${baseUrl}/part/65/pricing`);
  await page.getByText('Part: M2x4 SHCS').waitFor();
  await page.getByRole('tab', { name: 'Part Pricing' }).click();
  await page.getByLabel('Part Pricing').getByText('Part Pricing').waitFor();
  await page.getByRole('button', { name: 'Pricing Overview' }).waitFor();
  await page.getByText('Last Updated').waitFor();
  await page.getByRole('button', { name: 'Purchase History' }).isDisabled();
  await page.getByRole('button', { name: 'Internal Pricing' }).isEnabled();
  await page.getByRole('button', { name: 'Supplier Pricing' }).isDisabled();

  // Internal Pricing
  await page.getByRole('button', { name: 'Internal Pricing' }).click();
  await page.getByRole('button', { name: 'Price Break Not sorted' }).waitFor();

  // Internal Pricing - editing
  await page.getByRole('row', { name: '1 NZ$' }).getByRole('button').click();
  await page.getByRole('menuitem', { name: 'Edit' }).click();
  await page.getByText('Part *M2x4 SHCSSocket head').click();
  await page.getByText('Part *M2x4 SHCSSocket head').click();
  await page.getByRole('button', { name: 'Submit' }).isEnabled();
  await page.getByRole('button', { name: 'Submit' }).click();
});

test('PUI - Pages - Part - Pricing (Purchase)', async ({ page }) => {
  await doQuickLogin(page);

  // Part
  await page.goto(`${baseUrl}/part/69/pricing`);
  await page.getByText('Part: 530470210').waitFor();
  await page.getByRole('tab', { name: 'Part Pricing' }).click();
  await page.getByLabel('Part Pricing').getByText('Part Pricing').waitFor();
  await page.getByRole('button', { name: 'Pricing Overview' }).waitFor();
  await page.getByText('Last Updated').waitFor();
  await page.getByRole('button', { name: 'Purchase History' }).isEnabled();
  await page.getByRole('button', { name: 'Internal Pricing' }).isDisabled();
  await page.getByRole('button', { name: 'Supplier Pricing' }).isDisabled();

  // Purchase History
  await page.getByRole('button', { name: 'Purchase History' }).click();
  await page
    .getByRole('button', { name: 'Purchase Order Not sorted' })
    .waitFor();
  await page.getByText('	2022-04-29').waitFor();
});
