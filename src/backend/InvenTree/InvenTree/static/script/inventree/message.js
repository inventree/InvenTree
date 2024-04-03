/* exported
    showMessage,
    showAlertOrCache,
    showCachedAlerts,
*/

/*
 * Display an alert message at the top of the screen.
 * The message will contain a "close" button,
 * and also dismiss automatically after a certain amount of time.
 *
 * arguments:
 * - message: Text / HTML content to display
 *
 * options:
 * - style: alert style e.g. 'success' / 'warning'
 * - timeout: Time (in milliseconds) after which the message will be dismissed
 */
function showMessage(message, options={}) {

    var style = options.style || 'info';

    var timeout = options.timeout || 5000;

    var target = options.target || $('#alerts');

    var details = '';

    if (options.details) {
        details = `<p><small>${options.details}</p></small>`;
    }

    // Hacky function to get the next available ID
    var id = 1;

    while ($(`#alert-${id}`).exists()) {
        id++;
    }

    var icon = '';

    if (options.icon) {
        icon = `<span class='${options.icon}'></span>`;
    }

    // Construct the alert
    var html = `
    <div id='alert-${id}' class='alert alert-${style} alert-dismissible fade show' role='alert'>
        ${icon}
        <b>${message}</b>
        ${details}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
    `;

    target.append(html);

    // Remove the alert automatically after a specified period of time
    $(`#alert-${id}`).delay(timeout).slideUp(200, function() {
        $(this).alert(close);
    });
}


/*
 * Add a cached alert message to sesion storage
 */
function addCachedAlert(message, options={}) {

    var alerts = sessionStorage.getItem('inventree-alerts');

    if (alerts) {
        alerts = JSON.parse(alerts);
    } else {
        alerts = [];
    }

    alerts.push({
        message: message,
        style: options.style || 'success',
        icon: options.icon,
    });

    sessionStorage.setItem('inventree-alerts', JSON.stringify(alerts));
}


/*
 * Remove all cached alert messages
 */
function clearCachedAlerts() {
    sessionStorage.removeItem('inventree-alerts');
}


/*
 * Display an alert, or cache to display on reload
 */
function showAlertOrCache(message, cache, options={}) {

    if (cache) {
        addCachedAlert(message, options);
    } else {
        showMessage(message, options);
    }
}


/*
 * Display cached alert messages when loading a page
 */
function showCachedAlerts() {

    var alerts = JSON.parse(sessionStorage.getItem('inventree-alerts')) || [];

    alerts.forEach(function(alert) {

        showMessage(
            alert.message,
            {
                style: alert.style || 'success',
                icon: alert.icon,
            }
        );
    });

    clearCachedAlerts();
}