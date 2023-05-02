function updateDropDownItemsVisibility()
{
    var multipageWidgetNames = ['page_width', 'page_height',
                                'pagesize_preset', 'page_orientation',
                                'multipage_border'];
    multipageWidgetNames.forEach(function(widget) {
        if (django.jQuery('#id_multipage').prop("checked"))
            django.jQuery('.field-' + widget).show();
        else
            django.jQuery('.field-' + widget).hide();
    });
}

function updatePresetPageSize()
{
    var custom = true;
    django.jQuery("#id_pagesize_preset > option").each(function() {
        if (this.value != 'custom') {
            var landscapeGeom = (parseFloat(django.jQuery('#id_page_width').val()).toString() + "x" +
                   parseFloat(django.jQuery('#id_page_height').val()).toString());
            var portraitGeom = (parseFloat(django.jQuery('#id_page_height').val()).toString() + "x" +
                   parseFloat(django.jQuery('#id_page_width').val()).toString());
            if (this.value == landscapeGeom) {
                django.jQuery('#id_pagesize_preset').val(landscapeGeom);
                django.jQuery('#id_page_orientation').val('landscape');
                custom = false;
                return false;
            } else if (this.value == portraitGeom) {
                 django.jQuery('#id_pagesize_preset').val(portraitGeom);
                django.jQuery('#id_page_orientation').val('portrait');
                custom = false;
                return false;
            }
        }
    });

    if (custom)
        django.jQuery('#id_pagesize_preset ').val('custom');
}

function initPageSizeControls()
{
    django.jQuery("#id_pagesize_preset").on( "change", function() {
        if (django.jQuery(this).val() != 'custom') {
            var valParts = django.jQuery(this).val().split("x");
            if (django.jQuery('#id_page_orientation').find(":selected").val() == 'landscape') {
                django.jQuery("#id_page_width").val(valParts[0]);
                django.jQuery("#id_page_height").val(valParts[1]);
            } else {
                // portrait
                django.jQuery("#id_page_height").val(valParts[0]);
                django.jQuery("#id_page_width").val(valParts[1]);
            }
        }
    });

    django.jQuery("#id_page_orientation").on( "change", function() {
        if (django.jQuery("#id_pagesize_preset").val() != 'custom') {
            var valParts = django.jQuery("#id_pagesize_preset").val().split("x");
            if (django.jQuery(this).val() == 'portrait') {
                django.jQuery("#id_page_width").val(valParts[0]);
                django.jQuery("#id_page_height").val(valParts[1]);
            } else {
                // landscape
                django.jQuery("#id_page_height").val(valParts[0]);
                django.jQuery("#id_page_width").val(valParts[1]);
            }
        }
    });

    django.jQuery("#id_page_width").on( "change", function() {
        updatePresetPageSize();
    });

    django.jQuery("#id_page_height").on( "change", function() {
        updatePresetPageSize();
    });
}

window.addEventListener("load", function() {
    (function() {
        django.jQuery(document).ready(function(){
            updateDropDownItemsVisibility();
            django.jQuery('#id_multipage').click(function() {
                updateDropDownItemsVisibility();
            });
        })
    })(django.jQuery);
    updatePresetPageSize();
    initPageSizeControls();
});
