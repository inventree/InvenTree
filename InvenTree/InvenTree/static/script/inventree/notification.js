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

    $('#alerts').append(html);

    // Remove the alert automatically after a specified period of time
    $(`#alert-${id}`).delay(timeout).slideUp(200, function() {
        $(this).alert(close);
    });
}


/**
 * The notification checker is initiated when the document is loaded. It checks if there are unread notifications
 * if unread messages exist the alert flag is raised by making it visible
 **/
function notificationCheck() {
    // only refresh state if in focus
    if (document.hasFocus()) {
        inventreeGet(
            '/api/notifications/',
            {
                read: false,
            },
            {
                success: function(response) {
                    updateNotificationIndicator(response.length);
                }
            }
        );
    }
}

/**
 * handles read / unread buttons and UI rebuilding
 * 
 * arguments:
 * - btn: element that got clicked / fired the event -> must contain pk and target as attributes
 * 
 * options:
 * - panel_caller: this button was clicked in the notification panel
 **/
function updateNotificationReadState(btn, panel_caller=false) {
    var url = `/api/notifications/${btn.attr('pk')}/${btn.attr('target')}/`;

    inventreePut(url, {}, {
    method: 'POST',
    success: function() {
        // update the notification tables if they were declared
        if (window.updateNotifications) {
            window.updateNotifications();
        }

        // update current notification count
        var count = parseInt($("#notification-counter").html());
        if (btn.attr('target') == 'read') {
            count = count - 1;
        } else {
            count = count + 1;
        }
        // update notification indicator now
        updateNotificationIndicator(count);

        // remove notification if called from notification panel
        if (panel_caller) {
            btn.parent().parent().remove()
        }
    }
    });
};

/**
 * Returns the html for a read / unread button
 * 
 * arguments:
 * - pk: primary key of the notification
 * - state: current state of the notification (read / unread) -> just pass what you were handed by the api
 **/
function getReadEditButton(pk, state) {
    if (state) {
        var bReadText = '{% trans "Mark as unread" %}';
        var bReadIcon = 'fas fa-bookmark icon-red';
        var bReadTarget = 'unread';
    } else {
        var bReadText = '{% trans "Mark as read" %}';
        var bReadIcon = 'far fa-bookmark icon-green';
        var bReadTarget = 'read';
    }
    return `<button title='${bReadText}' class='notification-read btn btn-outline-secondary' type='button' pk='${pk}' target='${bReadTarget}'><span class='${bReadIcon}'></span></button>`;
}

/**
 * fills the notification panel when opened
 **/
function openNotificationPanel() {
    var html = '';
    var center_ref = '#notification-center';

    inventreeGet(
        '/api/notifications/',
        {
            read: false,
        },
        {
            success: function(response) {
                if (response.length == 0) {
                    html = `<p class='text-muted'>{% trans "No unread notifications" %}</p>`;
                } else {
                    // build up items
                    response.forEach(function(item, index) {
                        html += '<li class="list-group-item">';
                        // d-flex justify-content-between align-items-start
                        html += '<div>';
                        html += `<span class="badge rounded-pill bg-primary">${item.category}</span><span class="ms-2">${item.name}</span>`;
                        html += '</div>';
                        if (item.target) {
                            var link_text = `${item.target.model}: ${item.target.name}`;
                            if (item.target.link) {
                                link_text = `<a href='${item.target.link}'>${link_text}</a>`;
                            }
                            html += link_text
                        }
                        html += '<div>';
                        html += `<span class="text-muted">${item.age_human}</span>`;
                        html += getReadEditButton(item.pk, item.read);
                        html += "</div></li>";
                    });

                    // package up
                    html = `<ul class="list-group">${html}</ul>`
                }

                // set html
                $(center_ref).html(html);
            }
        }
    );

    $(center_ref).on('click', '.notification-read', function() {
        updateNotificationReadState($(this), true);
    });
}

/**
 * clears the notification panel when closed
 **/
function closeNotificationPanel() {
    $('#notification-center').html(`<p class='text-muted'>{% trans "Notifications will load here" %}</p>`);
}

/**
 * updates the notification counter
 **/
function updateNotificationIndicator(count) {
    if (count == 0) {
        $("#notification-alert").addClass("d-none");
    } else {
        $("#notification-alert").removeClass("d-none");
    }
    $("#notification-counter").html(count);
}
