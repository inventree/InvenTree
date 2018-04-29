function showAlert(target, message, timeout=5000) {

    $(target).find(".alert-msg").html(message);
    $(target).show();
    $(target).delay(timeout).slideUp(200, function() {
        $(this).alert(close);
    });
}