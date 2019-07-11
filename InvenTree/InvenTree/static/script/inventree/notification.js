function showAlert(target, message, timeout=5000) {

    $(target).find(".alert-msg").html(message);
    $(target).show();
    $(target).delay(timeout).slideUp(200, function() {
        $(this).alert(close);
    });
}

function showAlertOrCache(alertType, message, cache, timeout=5000) {
    if (cache) {
        sessionStorage.setItem("inventree-" + alertType, message);
    }
    else {
        showAlert('#' + alertType, message, timeout);
    }
}

function showCachedAlerts() {

    // Success Message
    if (sessionStorage.getItem("inventree-alert-success")) {
        showAlert("#alert-success", sessionStorage.getItem("inventree-alert-success"));
        sessionStorage.removeItem("inventree-alert-success");
    }

    // Info Message
    if (sessionStorage.getItem("inventree-alert-info")) {
        showAlert("#alert-info", sessionStorage.getItem("inventree-alert-info"));
        sessionStorage.removeItem("inventree-alert-info");
    }

    // Warning Message
    if (sessionStorage.getItem("inventree-alert-warning")) {
        showAlert("#alert-warning", sessionStorage.getItem("inventree-alert-warning"));
        sessionStorage.removeItem("inventree-alert-warning");
    }

    // Danger Message
    if (sessionStorage.getItem("inventree-alert-danger")) {
        showAlert("#alert-danger", sessionStorage.getItem("inventree-alert-danger"));
        sessionStorage.removeItem("inventree-alert-danger");
    }
}