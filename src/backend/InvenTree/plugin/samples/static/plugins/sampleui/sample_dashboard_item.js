/**
 * A sample dashboard item plugin for InvenTree.
 *
 * - This is a *very basic* example.
 * - In practice, you would want to use React / Mantine / etc to render more complex UI elements.
 */

export function renderDashboardItem(target, data) {

    if (!target) {
        console.error("No target provided to renderDashboardItem");
        return;
    }

    target.innerHTML = `
    <h4>Sample Dashboard Item</h4>
    <hr>
    <p>Hello world! This is a sample dashboard item loaded by the plugin system.</p>
    `;
}
