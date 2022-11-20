function updateDropDownItemsVisibility()
{
    if (django.jQuery('#id_is_dropdown').prop("checked"))
        django.jQuery('#partparametertemplatedropdownitem_set-group').show();
    else
        django.jQuery('#partparametertemplatedropdownitem_set-group').hide();
}

window.addEventListener("load", function() {
    (function() {
        django.jQuery(document).ready(function(){
            updateDropDownItemsVisibility();
            django.jQuery('#id_is_dropdown').click(function() {
                updateDropDownItemsVisibility();
            });
        })
    })(django.jQuery);
});
