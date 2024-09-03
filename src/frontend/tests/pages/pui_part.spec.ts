import { test } from '../baseFixtures';
import { baseUrl } from '../defaults';
import { doQuickLogin } from '../login';

test('PUI - Pages - Part - Locking', async ({ page }) => {
  await doQuickLogin(page);

  // Navigate to a known assembly which is *not* locked
  await page.goto(`${baseUrl}/part/104/bom`);
  await page.getByRole('tab', { name: 'Bill of Materials' }).click();
  await page.getByLabel('action-button-add-bom-item').waitFor();
  await page.getByRole('tab', { name: 'Parameters' }).click();
  await page.getByLabel('action-button-add-parameter').waitFor();

  // Navigate to a known assembly which *is* locked
  await page.goto(`${baseUrl}/part/100/bom`);
  await page.getByRole('tab', { name: 'Bill of Materials' }).click();
  await page.getByText('Locked', { exact: true }).waitFor();
  await page.getByText('Part is Locked', { exact: true }).waitFor();

  // Check the "parameters" tab also
  await page.getByRole('tab', { name: 'Parameters' }).click();
  await page.getByText('Part parameters cannot be').waitFor();
});

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
  let graph = page.getByLabel('pricing-overview-chart');
  await graph.waitFor();
  await graph.getByText('$60').waitFor();
  await graph.locator('tspan').filter({ hasText: 'BOM Pricing' }).waitFor();
  await graph.locator('tspan').filter({ hasText: 'Overall Pricing' }).waitFor();

  // BOM Pricing
  await page.getByRole('button', { name: 'BOM Pricing' }).click();
  await page.getByText('Bar Chart').click();
  await page.getByText('Pie Chart').click();
  await page.getByRole('button', { name: 'Quantity Not sorted' }).waitFor();
  await page.getByRole('button', { name: 'Unit Price Not sorted' }).waitFor();

  // BOM Pricing - linkjumping
  await page
    .getByLabel('BOM Pricing')
    .getByRole('table')
    .getByText('Wood Screw')
    .click();
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
  // await page.waitForURL('**/purchasing/supplier-part/697/');
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
  await page.getByText('2022-04-29').waitFor();
});

test('PUI - Pages - Part - Attachments', async ({ page }) => {
  await doQuickLogin(page);

  await page.goto(`${baseUrl}/part/69/attachments`);

  // Submit a new external link
  await page.getByLabel('action-button-add-external-').click();
  await page.getByLabel('text-field-link').fill('https://www.google.com');
  await page.getByLabel('text-field-comment').fill('a sample comment');

  // Note: Text field values are debounced for 250ms
  await page.waitForTimeout(500);

  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByRole('cell', { name: 'a sample comment' }).first().waitFor();

  // Launch dialog to upload a file
  await page.getByLabel('action-button-add-attachment').click();
  await page.getByLabel('text-field-comment').fill('some comment');
  await page.getByRole('button', { name: 'Cancel' }).click();
});

test('PUI - Pages - Part - Parameters', async ({ page }) => {
  await doQuickLogin(page);

  await page.goto(`${baseUrl}/part/69/parameters`);

  // Create a new template
  await page.getByLabel('action-button-add-parameter').click();

  // Select the "Color" parameter template (should create a "choice" field)
  await page.getByLabel('related-field-template').fill('Color');
  await page.getByRole('option', { name: 'Color Part color' }).click();
  await page.getByLabel('choice-field-data').click();
  await page.getByRole('option', { name: 'Green' }).click();

  // Select the "polarized" parameter template (should create a "checkbox" field)
  await page.getByLabel('related-field-template').fill('Polarized');
  await page.getByText('Is this part polarized?').click();
  await page
    .locator('label')
    .filter({ hasText: 'DataParameter Value' })
    .locator('div')
    .first()
    .click();

  await page.getByRole('button', { name: 'Cancel' }).click();
});

test('PUI - Pages - Part - Notes', async ({ page }) => {
  await doQuickLogin(page);

  await page.goto(`${baseUrl}/part/69/notes`);

  // Enable editing
  await page.getByLabel('Enable Editing').waitFor();

  // Use keyboard shortcut to "edit" the part
  await page.keyboard.press('Control+E');
  await page.getByLabel('text-field-name').waitFor();
  await page.getByLabel('text-field-description').waitFor();
  await page.getByLabel('related-field-category').waitFor();
  await page.getByRole('button', { name: 'Cancel' }).click();

  // Enable notes editing
  await page.getByLabel('Enable Editing').click();
  await page.getByLabel('Disable Editing').waitFor();
  await page.getByLabel('Save Notes').waitFor();
});

test('PUI - Pages - Part - 404', async ({ page }) => {
  await doQuickLogin(page);

  await page.goto(`${baseUrl}/part/99999/`);
  await page.getByText('Page Not Found', { exact: true }).waitFor();

  // Clear out any console error messages
  await page.evaluate(() => console.clear());
});

test('PUI - Pages - Part - Revision', async ({ page }) => {
  await doQuickLogin(page);

  await page.goto(`${baseUrl}/part/906/details`);

  await page.getByText('Revision of').waitFor();
  await page.getByText('Select Part Revision').waitFor();
  await page
    .getByText('Green Round Table (revision B) | B', { exact: true })
    .click();
  await page
    .getByRole('option', { name: 'Thumbnail Green Round Table No stock' })
    .click();

  await page.waitForURL('**/platform/part/101/**');
  await page.getByText('Select Part Revision').waitFor();
});
