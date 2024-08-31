/**
 * A sample panel plugin for InvenTree.
 *
 * This plugin file is dynamically loaded,
 * as specified in the plugin/samples/integration/user_interface_sample.py
 *
 * It provides a simple example of how panels can be dynamically rendered,
 * as well as dynamically hidden, based on the provided context.
 */

export function renderPanel(target, context) {

    if (!target) {
        console.error("No target provided to renderPanel");
        return;
    }

    target.innerHTML = `
    <h4>Dynamic Panel Content</h4>

    <p>This panel has been dynamically rendered by the plugin system.</p>
    <p>It can be hidden or displayed based on the provided context.</p>

    <hr>
    <h5>Context:</h5>

    <ul>
    <li>Username: ${context.user.username()}</li>
    <li>Is Staff: ${context.user.isStaff() ? "YES": "NO"}</li>
    <li>Model Type: ${context.model}</li>
    <li>Instance ID: ${context.id}</li>
    `;

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
