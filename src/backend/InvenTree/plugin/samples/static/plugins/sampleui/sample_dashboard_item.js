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


export function renderContextItem(target, data) {

    if (!target) {
        console.error("No target provided to renderContextItem");
        return;
    }

    let context = data?.context ?? {};

    let ctxString = '';

    for (let key in context) {
        ctxString += `<tr><td>${key}</td><td>${context[key]}</td></tr>`;
    }

    target.innerHTML = `
    <h4>Sample Context Item</h4>
    <hr>
    <p>Hello world! This is a sample context item loaded by the plugin system.</p>
    <table>
    <tbody>
    <tr><th>Item</th><th>Value</th></tr>
    ${ctxString}
    </tbody>
    </table>
    `;
}
