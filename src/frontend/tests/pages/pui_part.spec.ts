import { test } from '../baseFixtures';
import {
  clearTableFilters,
  getRowFromCell,
  loadTab,
  navigate
} from '../helpers';
import { doQuickLogin } from '../login';

/**
 * CHeck each panel tab for the "Parts" page
 */
test('Parts - Tabs', async ({ page }) => {
  await doQuickLogin(page);

  await page.getByRole('tab', { name: 'Parts' }).click();
  await page
    .getByLabel('panel-tabs-partcategory')
    .getByRole('tab', { name: 'Parts' })
    .click();

  // Select a particular part from the table
  await clearTableFilters(page);
  await page.getByPlaceholder('Search').fill('1551');
  await page.getByText('1551ABK').click();

  await loadTab(page, 'Allocations');
  await loadTab(page, 'Used In');
  await loadTab(page, 'Pricing');
  await loadTab(page, 'Suppliers');
  await loadTab(page, 'Purchase Orders');
  await loadTab(page, 'Scheduling');
  await loadTab(page, 'Stock History');
  await loadTab(page, 'Attachments');
  await loadTab(page, 'Notes');
  await loadTab(page, 'Related Parts');

  // Related Parts
  await page.getByText('1551ACLR').click();
  await loadTab(page, 'Part Details');
  await loadTab(page, 'Parameters');

  await page
    .getByLabel('panel-tabs-part')
    .getByRole('tab', { name: 'Stock', exact: true })
    .click();

  await loadTab(page, 'Allocations');
  await loadTab(page, 'Used In');
  await loadTab(page, 'Pricing');

  await navigate(page, 'part/category/index/parts');
  await page.getByText('Blue Chair').click();
  await loadTab(page, 'Bill of Materials');
  await loadTab(page, 'Build Orders');
});

test('Parts - Manufacturer Parts', async ({ page }) => {
  await doQuickLogin(page);

  await navigate(page, 'part/84/suppliers');

  await loadTab(page, 'Suppliers');
  await page.getByText('Hammond Manufacturing').click();
  await loadTab(page, 'Parameters');
  await loadTab(page, 'Suppliers');
  await loadTab(page, 'Attachments');
  await page.getByText('1551ACLR - 1551ACLR').waitFor();
});

test('Parts - Supplier Parts', async ({ page }) => {
  await doQuickLogin(page);

  await navigate(page, 'part/15/suppliers');

  await loadTab(page, 'Suppliers');
  await page.getByRole('cell', { name: 'DIG-84670-SJI' }).click();
  await loadTab(page, 'Received Stock'); //
  await loadTab(page, 'Purchase Orders');
  await loadTab(page, 'Pricing');
  await page.getByText('DIG-84670-SJI - R_550R_0805_1%').waitFor();
});

test('Parts - Locking', async ({ page }) => {
  await doQuickLogin(page);

  // Navigate to a known assembly which is *not* locked
  await navigate(page, 'part/104/bom');
  await loadTab(page, 'Bill of Materials');
  await page.getByLabel('action-button-add-bom-item').waitFor();
  await loadTab(page, 'Parameters');
  await page.getByLabel('action-button-add-parameter').waitFor();

  // Navigate to a known assembly which *is* locked
  await navigate(page, 'part/100/bom');
  await loadTab(page, 'Bill of Materials');
  await page.getByLabel('part-lock-icon').waitFor();
  await page.getByText('Part is Locked', { exact: true }).waitFor();

  // Check expected "badge" values
  await page.getByText('In Stock: 13').waitFor();
  await page.getByText('Required: 10').waitFor();
  await page.getByText('In Production: 50').waitFor();

  // Check the "parameters" tab also
  await loadTab(page, 'Parameters');
  await page.getByText('Part parameters cannot be').waitFor();
});

test('Parts - Allocations', async ({ page }) => {
  await doQuickLogin(page);

  // Let's look at the allocations for a single stock item
  await navigate(page, 'stock/item/324/');
  await loadTab(page, 'Allocations');

  await page.getByRole('button', { name: 'Build Order Allocations' }).waitFor();
  await page.getByRole('cell', { name: 'Making some blue chairs' }).waitFor();
  await page.getByRole('cell', { name: 'Making tables for SO 0003' }).waitFor();

  // Let's look at the allocations for an entire part
  await navigate(page, 'part/74/details');

  // Check that the overall allocations are displayed correctly
  await page.getByText('11 / ').waitFor();
  await page.getByText('5 / ').waitFor();

  // Navigate to the "Allocations" tab
  await loadTab(page, 'Allocations');

  await page.getByRole('button', { name: 'Build Order Allocations' }).waitFor();
  await page.getByRole('button', { name: 'Sales Order Allocations' }).waitFor();

  // Expected order reference values
  await page.getByText('BO0001').waitFor();
  await page.getByText('BO0016').waitFor();
  await page.getByText('BO0019').waitFor();
  await page.getByText('SO0008').waitFor();
  await page.getByText('SO0025').waitFor();

  // Check "progress" bar of BO0001
  const build_order_cell = await page.getByRole('cell', { name: 'BO0001' });
  const build_order_row = await getRowFromCell(build_order_cell);
  await build_order_row.getByText('11 / 75').waitFor();

  // Expand allocations against BO0001
  await build_order_cell.click();
  await page.getByRole('cell', { name: '# 3', exact: true }).waitFor();
  await page.getByRole('cell', { name: 'Room 101', exact: true }).waitFor();
  await build_order_cell.click();

  // Check row options for BO0001
  await build_order_row.getByLabel(/row-action-menu/).click();
  await page.getByRole('menuitem', { name: 'View Build Order' }).waitFor();
  await page.keyboard.press('Escape');

  // Check "progress" bar of SO0025
  const sales_order_cell = await page.getByRole('cell', { name: 'SO0025' });
  const sales_order_row = await getRowFromCell(sales_order_cell);
  await sales_order_row.getByText('3 / 10').waitFor();

  // Expand allocations against SO0025
  await sales_order_cell.click();
  await page.getByRole('cell', { name: '161', exact: true });
  await page.getByRole('cell', { name: '169', exact: true });
  await page.getByRole('cell', { name: '170', exact: true });
  await sales_order_cell.click();

  // Check row options for SO0025
  await sales_order_row.getByLabel(/row-action-menu/).click();
  await page.getByRole('menuitem', { name: 'View Sales Order' }).waitFor();
  await page.keyboard.press('Escape');
});

test('Parts - Pricing (Nothing, BOM)', async ({ page }) => {
  await doQuickLogin(page);

  // Part with no history
  await navigate(page, 'part/82/pricing');

  await page.getByText('Small plastic enclosure, black').waitFor();
  await loadTab(page, 'Part Pricing');
  await page.getByLabel('Part Pricing').getByText('Part Pricing').waitFor();
  await page.getByRole('button', { name: 'Pricing Overview' }).waitFor();
  await page.getByText('Last Updated').waitFor();
  await page.getByRole('button', { name: 'Purchase History' }).isDisabled();
  await page.getByRole('button', { name: 'Internal Pricing' }).isDisabled();
  await page.getByRole('button', { name: 'Supplier Pricing' }).isDisabled();

  // Part with history
  await navigate(page, 'part/108/pricing');
  await page.getByText('A chair - with blue paint').waitFor();
  await loadTab(page, 'Part Pricing');
  await page.getByLabel('Part Pricing').getByText('Part Pricing').waitFor();
  await page.getByRole('button', { name: 'Pricing Overview' }).waitFor();
  await page.getByText('Last Updated').waitFor();
  await page.getByRole('button', { name: 'Internal Pricing' }).isDisabled();
  await page.getByRole('button', { name: 'Sale History' }).isDisabled();
  await page.getByRole('button', { name: 'Sale Pricing' }).isDisabled();
  await page.getByRole('button', { name: 'BOM Pricing' }).isEnabled();

  // Overview Graph
  const graph = page.getByLabel('pricing-overview-chart');
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
  await page.waitForURL('**/part/98/**');
});

test('Parts - Pricing (Supplier)', async ({ page }) => {
  await doQuickLogin(page);

  // Part
  await navigate(page, 'part/55/pricing');
  await page.getByText('Ceramic capacitor, 100nF in').waitFor();
  await loadTab(page, 'Part Pricing');
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
  const target = page.getByText('ARR-26041-LPC').first();
  await target.waitFor();
  await target.click();
  // await page.waitForURL('**/purchasing/supplier-part/697/');
});

test('Parts - Pricing (Variant)', async ({ page }) => {
  await doQuickLogin(page);

  // Part
  await navigate(page, 'part/106/pricing');
  await page.getByText('A chair - available in multiple colors').waitFor();
  await loadTab(page, 'Part Pricing');
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
  const target = page.getByText('Green Chair').first();
  await target.waitFor();
  await target.click();
  await page.waitForURL('**/part/109/**');
});

test('Parts - Pricing (Internal)', async ({ page }) => {
  await doQuickLogin(page);

  // Part
  await navigate(page, 'part/65/pricing');
  await page.getByText('Socket head cap screw, M2').waitFor();
  await loadTab(page, 'Part Pricing');
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

test('Parts - Pricing (Purchase)', async ({ page }) => {
  await doQuickLogin(page);

  // Part
  await navigate(page, 'part/69/pricing');
  await page.getByText('1.25mm Pitch, PicoBlade PCB').waitFor();
  await loadTab(page, 'Part Pricing');
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

test('Parts - Attachments', async ({ page }) => {
  await doQuickLogin(page);

  await navigate(page, 'part/69/attachments');

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

test('Parts - Parameters', async ({ page }) => {
  await doQuickLogin(page);

  await navigate(page, 'part/69/parameters');

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

test('Parts - Notes', async ({ page }) => {
  await doQuickLogin(page);

  await navigate(page, 'part/69/notes');

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

  await page.getByLabel('Save Notes').waitFor();
  await page.getByLabel('Close Editor').waitFor();
});

test('Parts - 404', async ({ page }) => {
  await doQuickLogin(page);

  await navigate(page, 'part/99999/');
  await page.getByText('Page Not Found', { exact: true }).waitFor();

  // Clear out any console error messages
  await page.evaluate(() => console.clear());
});

test('Parts - Revision', async ({ page }) => {
  await doQuickLogin(page);

  await navigate(page, 'part/906/details');

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
