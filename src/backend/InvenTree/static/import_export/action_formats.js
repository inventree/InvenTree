(function($) {
  $(document).ready(function() {
    var $actionsSelect, $formatsElement;
    if ($('body').hasClass('grp-change-list')) {
        // using grappelli
        $actionsSelect = $('#grp-changelist-form select[name="action"]');
        $formatsElement = $('#grp-changelist-form select[name="file_format"]');
    } else {
        // using default admin
        $actionsSelect = $('#changelist-form select[name="action"]');
        $formatsElement = $('#changelist-form select[name="file_format"]').parent();
    }
    $actionsSelect.change(function() {
      if ($(this).val() === 'export_admin_action') {
        $formatsElement.show();
      } else {
        $formatsElement.hide();
      }
    });
    $actionsSelect.change();
  });
})(django.jQuery);
