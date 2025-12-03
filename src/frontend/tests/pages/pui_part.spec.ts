import { test } from '../baseFixtures';
import {
  clearTableFilters,
  clickOnParamFilter,
  clickOnRowMenu,
  deletePart,
  getRowFromCell,
  loadTab,
  navigate,
  setTableChoiceFilter
} from '../helpers';
import { doCachedLogin } from '../login';
import { setPluginState, setSettingState } from '../settings';

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
  const page = await doCachedLogin(browser, {
    url: 'part/category/index/parts'
  });

  // Display all active assemblies with validated BOMs
  await clearTableFilters(page);
  await setTableChoiceFilter(page, 'assembly', 'Yes');
  await setTableChoiceFilter(page, 'active', 'Yes');
  await setTableChoiceFilter(page, 'BOM Valid', 'Yes');

  // Navigate to BOM for a particular assembly
  await navigate(page, 'part/87/bom');
  await loadTab(page, 'Bill of Materials');

  // Mouse-hover to display BOM validation info for this assembly
  await page.getByRole('button', { name: 'bom-validation-info' }).hover();
  await page
    .getByText('The Bill of Materials for this part has been validated')
    .waitFor();
  await page.getByText('Validated On: 2025-07-23').waitFor();
  await page.getByText('Robert Shuruncle').waitFor();

  // Move the mouse away
  await page.getByRole('link', { name: 'Bill of Materials' }).hover();

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

  const keywords = await page
    .getByLabel('text-field-keywords', { exact: true })
    .inputValue();
  await page
    .getByLabel('text-field-keywords', { exact: true })
    .fill(keywords ? '' : 'table furniture');

  // Test URL validation
  await page
    .getByRole('textbox', { name: 'text-field-link', exact: true })
    .fill('htxp-??QQQ++');
  await page.waitForTimeout(200);
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Enter a valid URL.').waitFor();

  // Fill with an empty URL
  const description = await page
    .getByLabel('text-field-description', { exact: true })
    .inputValue();

  await page
    .getByRole('textbox', { name: 'text-field-link', exact: true })
    .fill('');
  await page
    .getByLabel('text-field-description', { exact: true })
    .fill(`${description}+`);
  await page.waitForTimeout(200);
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByText('Item Updated').waitFor();
});

test('Parts - Locking', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'part/104/bom' });

  await loadTab(page, 'Bill of Materials');
  await page
    .getByRole('button', { name: 'action-menu-add-bom-items' })
    .waitFor();

  await loadTab(page, 'Parameters');
  await page
    .getByRole('button', { name: 'action-menu-add-parameters' })
    .click();
  await page
    .getByRole('menuitem', {
      name: 'action-menu-add-parameters-create-parameter'
    })
    .click();

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

  // Depending on the state of other tests, the "In Production" value may vary
  // This could be either 4 / 49, or 5 / 49
  await page.getByText(/[4|5] \/ \d+/).waitFor();

  // Badges
  await page.getByText('Required: 10').waitFor();
  await page.getByText('No Stock').waitFor();
  await page.getByText(/In Production: [4|5]/).waitFor();

  await page.getByText('Creation Date').waitFor();
  await page.getByText('2022-04-29').waitFor();
});

test('Parts - Requirements', async ({ browser }) => {
  // Navigate to the "Widget Assembly" part detail page
  // This part has multiple "variants"
  // We expect that the template page includes variant requirements
  const page = await doCachedLogin(browser, { url: 'part/77/details' });

  // Check top-level badges
  await page.getByText('In Stock: 209').waitFor();
  await page.getByText('Available: 204').waitFor();
  await page.getByText(/Required: 2\d+/).waitFor();
  await page.getByText('In Production: 24').waitFor();

  // Check requirements details
  await page.getByText('204 / 209').waitFor(); // Available stock
  await page.getByText(/0 \/ 1\d+/).waitFor(); // Allocated to build orders
  await page.getByText('5 / 175').waitFor(); // Allocated to sales orders
  await page.getByText(/24 \/ 2\d+/).waitFor(); // In production

  // Let's check out the "variants" for this part, too
  await navigate(page, 'part/81/details'); // WID-REV-A
  await page.getByText('WID-REV-A', { exact: true }).first().waitFor();
  await page.getByText('In Stock: 165').waitFor();
  await page.getByText('Required: 75').waitFor();

  await navigate(page, 'part/903/details'); // WID-REV-B
  await page.getByText('WID-REV-B', { exact: true }).first().waitFor();

  await page.getByText('In Stock: 44').waitFor();
  await page.getByText('Available: 39').waitFor();
  await page.getByText('Required: 100').waitFor();
  await page.getByText('In Production: 10').waitFor();

  await page.getByText('39 / 44').waitFor(); // Available stock
  await page.getByText('5 / 100').waitFor(); // Allocated to sales orders
  await page.getByText('10 / 125').waitFor(); // In production

  // Also check requirements for part with open build orders which have been partially consumed
  await navigate(page, 'part/105/details');

  await page.getByText('Required: 2').waitFor();
  await page.getByText('Available: 32').waitFor();
  await page.getByText('In Stock: 34').waitFor();
  await page.getByText('2 / 2').waitFor(); // Allocated to build orders
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
  await page.getByText('Last Updated').first().waitFor();
  await page.getByRole('button', { name: 'Internal Pricing' }).isEnabled();
  await page.getByRole('button', { name: 'BOM Pricing' }).isEnabled();
  await page.getByRole('button', { name: 'Variant Pricing' }).isEnabled();

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
  await page
    .getByLabel('text-field-link', { exact: true })
    .fill('https://www.google.com');
  await page
    .getByLabel('text-field-comment', { exact: true })
    .fill('a sample comment');

  // Note: Text field values are debounced for 250ms
  await page.waitForTimeout(300);

  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByRole('cell', { name: 'a sample comment' }).first().waitFor();

  // Launch dialog to upload a file
  await page.getByLabel('action-button-add-attachment').click();
  await page
    .getByLabel('text-field-comment', { exact: true })
    .fill('some comment');
  await page.getByRole('button', { name: 'Cancel' }).click();
});

test('Parts - Parameters', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'part/69/parameters' });

  // Create a new template
  await page
    .getByRole('button', { name: 'action-menu-add-parameters' })
    .click();
  await page
    .getByRole('menuitem', {
      name: 'action-menu-add-parameters-create-parameter'
    })
    .click();

  // Select the "Color" parameter template (should create a "choice" field)
  await page.getByLabel('related-field-template').fill('Color');
  await page.getByRole('option', { name: 'Color Part color' }).click();
  await page.getByLabel('choice-field-data').click();
  await page.getByRole('option', { name: 'Green' }).click();

  await page
    .getByLabel('text-field-note', { exact: true })
    .fill('A custom note field');

  // Select the "polarized" parameter template (should create a "checkbox" field)
  await page.getByLabel('related-field-template').fill('Polarized');
  await page.getByRole('option', { name: 'Polarized Is this part' }).click();

  // Submit with "false" value
  await page.getByRole('button', { name: 'Submit' }).click();

  const cell = await page.getByRole('cell', {
    name: 'Is this part polarized?'
  });

  // Check for the expected values in the table
  const row = await getRowFromCell(cell);

  await row.getByRole('cell', { name: 'No', exact: true }).waitFor();
  await row.getByRole('cell', { name: 'allaccess' }).waitFor();
  await row.getByLabel(/row-action-menu-/i).click();
  await page.getByRole('menuitem', { name: 'Edit' }).click();

  // Toggle false to true
  await page
    .locator('label')
    .filter({ hasText: 'DataParameter Value' })
    .locator('div')
    .first()
    .click();
  await page.getByRole('button', { name: 'Submit' }).click();

  // Finally, delete the parameter
  await row.getByLabel(/row-action-menu-/i).click();
  await page.getByRole('menuitem', { name: 'Delete' }).click();

  await page.getByRole('button', { name: 'Delete', exact: true }).click();
  await page.getByText('No records found').first().waitFor();
});

test('Parts - Parameter Filtering', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'part/' });

  await loadTab(page, 'Parts', true);
  await page
    .getByRole('button', { name: 'segmented-icon-control-parametric' })
    .click();

  await clearTableFilters(page);

  // All parts should be available (no filters applied)
  await page.getByText(/\/ 42\d/).waitFor();

  const clearParamFilter = async (name: string) => {
    await clickOnParamFilter(page, name);
    await page.getByLabel(`clear-filter-${name}`).waitFor();
    await page.getByLabel(`clear-filter-${name}`).click();
    // await page.getByLabel(`clear-filter-${name}`).click();
  };

  // Let's filter by color
  await clickOnParamFilter(page, 'Color');
  await page.getByRole('option', { name: 'Red' }).click();

  // Only 10 parts available
  await page.getByText('/ 10').waitFor();

  // Reset the filter
  await clearParamFilter('Color');

  await page.getByText(/\/ 42\d/).waitFor();
});

test('Parts - Test Results', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: '/part/74/test_results' });

  await page.waitForTimeout(2500);

  await page.getByText(/1 - \d+ \/ 1\d\d/).waitFor();
  await page.getByText('Blue Paint Applied').waitFor();
});

test('Parts - Notes', async ({ browser }) => {
  const page = await doCachedLogin(browser, { url: 'part/69/notes' });

  // Enable editing
  await page.getByLabel('Enable Editing').waitFor();

  // Use keyboard shortcut to "edit" the part
  await page.keyboard.press('Control+E');
  await page.getByLabel('text-field-name', { exact: true }).waitFor();
  await page.getByLabel('text-field-description', { exact: true }).waitFor();
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
  await page.waitForTimeout(250);

  await page.getByRole('option', { name: '- Furniture/Chairs' }).click();
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

test('Parts - Import supplier part', async ({ browser }) => {
  const page = await doCachedLogin(browser, {
    url: 'part/category/1/parts'
  });

  // Ensure that the sample supplier plugin is enabled
  await setPluginState({
    plugin: 'samplesupplier',
    state: true
  });

  await setSettingState({
    setting: 'SUPPLIER',
    value: 3,
    type: 'plugin',
    plugin: 'samplesupplier'
  });

  // cleanup old imported part if it exists
  await deletePart('BOLT-Steel-M5-5');
  await deletePart('BOLT-M5-5');

  await page.reload();
  await page.waitForLoadState('networkidle');

  // Open "Add parts" menu
  await page.getByRole('button', { name: 'action-menu-add-parts' }).click();

  await page
    .getByRole('menuitem', { name: 'action-menu-add-parts-create-part' })
    .waitFor();
  await page
    .getByRole('menuitem', { name: 'action-menu-add-parts-import-from-file' })
    .waitFor();
  await page
    .getByRole('menuitem', {
      name: 'action-menu-add-parts-import-from-supplier'
    })
    .click();

  await page
    .getByRole('textbox', { name: 'textbox-search-for-part' })
    .fill('M5');
  await page.waitForTimeout(250);
  await page
    .getByRole('textbox', { name: 'textbox-search-for-part' })
    .press('Enter');

  await page.getByText('Bolt M5x5mm Steel').waitFor();
  await page
    .getByRole('button', { name: 'action-button-import-part-BOLT-Steel-M5-5' })
    .click();
  await page.waitForTimeout(250);
  await page
    .getByRole('button', { name: 'action-button-import-part-now' })
    .click();

  await page
    .getByRole('button', { name: 'action-button-import-create-parameters' })
    .dispatchEvent('click');
  await page
    .getByRole('button', { name: 'action-button-import-stock-next' })
    .dispatchEvent('click');
  await page
    .getByRole('button', { name: 'action-button-import-close' })
    .dispatchEvent('click');

  // cleanup imported part if it exists
  await deletePart('BOLT-Steel-M5-5');
  await deletePart('BOLT-M5-5');
});
