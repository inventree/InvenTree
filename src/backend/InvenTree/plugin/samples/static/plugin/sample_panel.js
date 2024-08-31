/**
 * A sample panel plugin for InvenTree.
 *
 * This plugin file is dynamically loaded,
 * as specified in the plugin/samples/integration/user_interface_sample.py
 *
 * It provides a simple example of how panels can be dynamically rendered,
 * as well as dynamically hidden, based on the provided context.
 */

export function renderPanel(context) {

    const target = context.target;

    if (!target) {
        console.error("No target provided to renderPanel");
        return;
    }

    target.innerHTML = `
    <h4>Dynamic Panel Content</h4>

    <p>This panel has been dynamically rendered by the plugin system.</p>
    <p>It can be hidden or displayed based on the provided context.</p>
    `;

    console.log("renderPanel:", context);
}


// Dynamically hide the panel based on the provided context
export function isPanelHidden(context) {
    console.log("isPanelHidden:");
    console.log("context:", context);

    return false;
}
