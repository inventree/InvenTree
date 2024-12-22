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
    <h4>Admin Item</h4>
    <hr>
    <p>Hello there, admin user!</p>
    `;
}
