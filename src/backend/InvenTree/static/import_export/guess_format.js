(function($) {
  $().ready(function () {
    $('input.guess_format[type="file"]').change(function () {
      var files = this.files;
      var dropdowns = $(this.form).find('select.guess_format');
      if(files.length > 0) {
        var extension = files[0].name.split('.').pop().trim().toLowerCase();
        for(var i = 0; i < dropdowns.length; i++) {
          var dropdown = dropdowns[i];
          dropdown.selectedIndex = 0;
          for(var j = 0; j < dropdown.options.length; j++) {
            if(extension === dropdown.options[j].text.trim().toLowerCase()) {
              dropdown.selectedIndex = j;
              break;
            }
          }
        }
      }
    });
  });
})(django.jQuery);
