import { test } from '../baseFixtures';
import {
  clearTableFilters,
  clickOnRowMenu,
  getRowFromCell,
  loadTab,
  navigate
} from '../helpers';
import { doCachedLogin } from '../login';

/**
 * CHeck each panel tab for the "Parts" page
 */
test('Parts - Tabs', async ({ browser }) => {
  const page = await doCachedLogin(browser);

  await page.getByRole('tab', { name: 'Parts' }).click();
  await page.waitForURL('**/part/category/index/**');

  await page
    .getByLabel('panel-tabs-partcategory')
    .getByRole('tab', { name: 'Parts' })
    .click();

  // Select a particular part from the table
  await clearTableFilters(page);
  await page.getByPlaceholder('Search').fill('1551');
  await page.waitForLoadState('networkidle');
  await page.getByText('1551ABK').click();

  await loadTab(page, 'Allocations');
  await loadTab(page, 'Used In');
  await loadTab(page, 'Pricing');
  await loadTab(page, 'Suppliers');
  await loadTab(page, 'Purchase Orders');
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

test('Parts - Manufacturer Parts', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'part/84/suppliers' });

  await loadTab(page, 'Suppliers');
  await page.getByText('Hammond Manufacturing').click();
  await loadTab(page, 'Parameters');
  await loadTab(page, 'Suppliers');
  await loadTab(page, 'Attachments');
  await page.getByText('1551ACLR - 1551ACLR').waitFor();
});

test('Parts - Supplier Parts', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'part/15/suppliers' });

  await loadTab(page, 'Suppliers');
  await page.getByRole('cell', { name: 'DIG-84670-SJI' }).click();
  await loadTab(page, 'Received Stock'); //
  await loadTab(page, 'Purchase Orders');
  await loadTab(page, 'Pricing');
  await page.getByText('DIG-84670-SJI - R_550R_0805_1%').waitFor();
});

test('Parts - BOM', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'part/87/bom' });

  await loadTab(page, 'Bill of Materials');
  await page.waitForLoadState('networkidle');

  const cell = await page.getByRole('cell', {
    name: 'Small plastic enclosure, black',
    exact: true
  });

  await clickOnRowMenu(cell);

  // Check for expected context menu actions
  await page.getByRole('menuitem', { name: 'Edit', exact: true }).waitFor();
  await page.getByRole('menuitem', { name: 'Delete', exact: true }).waitFor();

  await page
    .getByRole('menuitem', { name: 'Edit Substitutes', exact: true })
    .click();
  await page.getByText('Edit BOM Substitutes').waitFor();
  await page.getByText('1551ACLR').first().waitFor();
  await page.getByText('1551AGY').first().waitFor();

  await page.getByLabel('related-field-part').fill('enclosure');
  await page.getByText('1591BTBU').click();

  await page.getByRole('button', { name: 'Add Substitute' }).waitFor();
  await page.getByRole('button', { name: 'Close' }).click();
});

test('Part - Editing', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'part/104/details' });

  await page.getByText('A square table - with blue paint').first().waitFor();

  // Open part edit dialog
  await page.keyboard.press('Control+E');

  const keywords = await page.getByLabel('text-field-keywords').inputValue();
  await page
    .getByLabel('text-field-keywords')
    .fill(keywords ? '' : 'table furniture');

  // Test URL validation
  await page
    .getByRole('textbox', { name: 'text-field-link' })
    .fill('htxp-??QQQ++');
  await page.waitForTimeout(200);
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Enter a valid URL.').waitFor();

  // Fill with an empty URL
  const description = await page
    .getByLabel('text-field-description')
    .inputValue();

  await page.getByRole('textbox', { name: 'text-field-link' }).fill('');
  await page.getByLabel('text-field-description').fill(`${description}+`);
  await page.waitForTimeout(200);
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Item Updated').waitFor();
});

test('Parts - Locking', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'part/104/bom' });
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

test('Parts - Details', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'part/113/details' });

  // Check for expected values on this page
  await page.getByText('Required for Orders').waitFor();
  await page.getByText('Allocated to Sales Orders').waitFor();
  await page.getByText('Can Build').waitFor();

  await page.getByText('0 / 10').waitFor();
  await page.getByText('4 / 49').waitFor();

  // Badges
  await page.getByText('Required: 10').waitFor();
  await page.getByText('No Stock').waitFor();
  await page.getByText('In Production: 4').waitFor();

  await page.getByText('Creation Date').waitFor();
  await page.getByText('2022-04-29').waitFor();
});

test('Parts - Allocations', async ({ browser }) => {
  // Let's look at the allocations for a single stock item
  const page = await doCachedLogin(browser, { url: 'stock/item/324/' });
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

test('Parts - Pricing (Nothing, BOM)', async ({ browser }) => {
  // Part with no history
  const page = await doCachedLogin(browser, { url: 'part/82/pricing' });

  await page.getByText('Small plastic enclosure, black').waitFor();
  await loadTab(page, 'Part Pricing');
  await page.getByLabel('Part Pricing').getByText('Part Pricing').waitFor();
  await page.getByRole('button', { name: 'Pricing Overview' }).waitFor();
  await page.getByText('Last Updated').waitFor();
  await page.getByRole('button', { name: 'Purchase History' }).isDisabled();
  await page.getByRole('button', { name: 'Internal Pricing' }).isDisabled();
  await page.getByRole('button', { name: 'Supplier Pricing' }).isDisabled();

  // Part with history
  await navigate(page, 'part/108/pricing', { waitUntil: 'networkidle' });
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

test('Parts - Pricing (Supplier)', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'part/55/pricing' });

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

test('Parts - Pricing (Variant)', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'part/106/pricing' });
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

test('Parts - Pricing (Internal)', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'part/65/pricing' });
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

test('Parts - Pricing (Purchase)', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'part/69/pricing' });

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

test('Parts - Attachments', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'part/69/attachments' });

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

test('Parts - Parameters', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'part/69/parameters' });

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

test('Parts - Parameter Filtering', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'part/' });

  await loadTab(page, 'Part Parameters');
  await clearTableFilters(page);

  // All parts should be available (no filters applied)
  await page.getByText('/ 425').waitFor();

  const clickOnParamFilter = async (name: string) => {
    const button = await page
      .getByRole('button', { name: `${name} Not sorted` })
      .getByRole('button')
      .first();
    await button.scrollIntoViewIfNeeded();
    await button.click();
  };

  const clearParamFilter = async (name: string) => {
    await clickOnParamFilter(name);
    await page.getByLabel(`clear-filter-${name}`).click();
  };

  // Let's filter by color
  await clickOnParamFilter('Color');
  await page.getByRole('option', { name: 'Red' }).click();

  // Only 10 parts available
  await page.getByText('/ 10').waitFor();

  // Reset the filter
  await clearParamFilter('Color');
  await page.getByText('/ 425').waitFor();
});

test('Parts - Notes', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'part/69/notes' });

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

test('Parts - 404', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'part/99999/' });
  await page.getByText('Page Not Found', { exact: true }).waitFor();

  // Clear out any console error messages
  await page.evaluate(() => console.clear());
});

test('Parts - Revision', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'part/906/details' });

  await page.getByText('Revision of').waitFor();
  await page.getByText('Select Part Revision').waitFor();
  await page
    .getByText('Green Round Table (revision B) | B', { exact: true })
    .click();
  await page
    .getByRole('option', { name: 'Thumbnail Green Round Table No stock' })
    .click();

  await page.waitForURL('**/web/part/101/**');
  await page.getByText('Select Part Revision').waitFor();
});

test('Parts - Bulk Edit', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'part/category/index/parts'
  });

  // Edit the category for multiple parts
  await page.getByLabel('Select record 1', { exact: true }).click();
  await page.getByLabel('Select record 2', { exact: true }).click();
  await page.getByLabel('action-menu-part-actions').click();
  await page.getByLabel('action-menu-part-actions-set-category').click();
  await page.getByLabel('related-field-category').fill('rnitu');
  await page
    .getByRole('option', { name: '- Furniture/Chairs' })
    .getByRole('paragraph')
    .click();

  await page.getByRole('button', { name: 'Update' }).click();
  await page.getByText('Items Updated').waitFor();
});

test('Parts - Duplicate', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'part/74/details'
  });

  // Open "duplicate part" dialog
  await page.getByLabel('action-menu-part-actions').click();
  await page.getByLabel('action-menu-part-actions-duplicate').click();

  // Check for expected fields
  await page.getByText('Copy Image', { exact: true }).waitFor();
  await page.getByText('Copy Notes', { exact: true }).waitFor();
  await page.getByText('Copy Parameters', { exact: true }).waitFor();
  await page.getByText('Copy Tests', { exact: true }).waitFor();
});
