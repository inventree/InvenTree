/**
 * A sample panel plugin for InvenTree.
 *
 * This plugin file is dynamically loaded,
 * as specified in the plugin/samples/integration/user_interface_sample.py
 *
 * It provides a simple example of how panels can be dynamically rendered,
 * as well as dynamically hidden, based on the provided context.
 */

export function renderPanel(target, data) {

    if (!target) {
        console.error("No target provided to renderPanel");
        return;
    }

    target.innerHTML = `
    <h4>Dynamic Panel Content</h4>

    <p>This panel has been dynamically rendered by the plugin system.</p>
    <p>It can be hidden or displayed based on the provided context.</p>

    <hr>
    <h5>Client Context:</h5>

    <ul>
    <li>Username: ${data.user.username()}</li>
    <li>Is Staff: ${data.user.isStaff() ? "YES": "NO"}</li>
    <li>Model Type: ${data.model}</li>
    <li>Instance ID: ${data.id}</li>
    </ul>
    <hr>
    <h5>Server Context:</h5>
    <ul>
    <li>Server Version: ${data.context.version}</li>
    <li>Plugin Version: ${data.context.plugin_version}</li>
    <li>Random Number: ${data.context.random}</li>
    <li>Time: ${data.context.time}</li>
    </ul>
    `;

}


/**
 * Render a panel on a Part detail page
 */
export function renderPartPanel(target, data) {

    if (!target) {
        console.error("No target provided to renderPartPanel");
        return;
    }

    target.innerHTML = `
    <h4>Part Detail Panel</h4>
    <hr>
    <p>This is a custom panel for a Part detail page</p>
    `;
}



/**
 * Render a panel on a PurchaseOrder detail page
 */
export function renderPoPanel(target, data) {
    if (!target) {
        console.error("No target provided to renderPoPanel");
        return;
    }

    target.innerHTML = `
    <h4>Order Reference: ${data.instance?.reference}</h4>
    <hr>
    <p>This is a custom panel for a PurchaseOrder detail page</p>
    `;
}


/**
 * Render a panel that is only visible to admin users
 */
export function renderAdminOnlyPanel(target, data) {
    if (!target) {
        console.error("No target provided to renderAdminOnlyPanel");
        return;
    }

    target.innerHTML = `Hello Admin user! This panel is only visible to admin users.`;
}


// Dynamically hide the panel based on the provided context
export function isPanelHidden(context) {

    // Hide the panel if the user is not staff
    if (!context?.user?.isStaff()) {
        return true;
    }

    // Only display for active parts
    return context.model != 'part' || !context.instance || !context.instance.active;
}
