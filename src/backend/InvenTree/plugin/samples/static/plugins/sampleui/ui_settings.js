

export function renderPluginSettings(target, data) {

    console.log("renderPluginSettings:", data);

    target.innerHTML = `
    <h4>Custom Plugin Configuration Content</h4>
    <p>Custom plugin configuration UI elements can be rendered here.</p>

    <p>The following context data was provided by the server:</p>
    <ul>
    ${Object.entries(data.context).map(([key, value]) => `<li>${key}: ${value}</li>`).join('')}
    </ul>
    `;
}
