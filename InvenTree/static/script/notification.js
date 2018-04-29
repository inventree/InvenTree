function showAlert(target, message, timeout=5000) {

    $(target).find(".alert-msg").html(message);
    $(target).show();
    $(target).delay(timeout).slideUp(200, function() {
        $(this).alert(close);
    });
}

function showCachedAlerts() {

    // Success Message
    if (sessionStorage.getItem("alert-success")) {
        showAlert("#alert-success", sessionStorage.getItem("alert-success"));
        sessionStorage.removeItem("alert-success");
    }

    // Info Message
    if (sessionStorage.getItem("alert-info")) {
        showAlert("#alert-info", sessionStorage.getItem("alert-info"));
        sessionStorage.removeItem("alert-info");
    }

    // Warning Message
    if (sessionStorage.getItem("alert-warning")) {
        showAlert("#alert-warning", sessionStorage.getItem("alert-warning"));
        sessionStorage.removeItem("alert-warning");
    }

    // Danger Message
    if (sessionStorage.getItem("alert-danger")) {
        showAlert("#alert-danger", sessionStorage.getItem("alert-danger"));
        sessionStorage.removeItem("alert-danger");
    }

    sessionStorage.setItem("alert-danger", 'test');
}