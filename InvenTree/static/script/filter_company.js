var keyDelay = 0;

var delay = (function(){
    return function(callback, ms){
        clearTimeout(keyDelay);
        keyDelay = setTimeout(callback, ms);
    };
})();


function add_company(company){

    var text = "<li class='list-group-item'>";

    text += "<b><a href='" + company.url + "'>";
    text += company.name + "</a></b>";

    if (company.description){
        text += " - " + company.description;
    }

    text += "</li>";

    $("#company-list").append(text);
}


function filter(text){

    $.ajax(
        {
            url: "/api/company/",
            success: function(result) {
                $("#company-list").empty();
                $.each(result.results, function(i, company){
                    add_company(company);
                })
            },
            data: {
                'search': text,
            }
        }
    );
}

$(document).ready(function(){
  $("#company-filter").keyup(function(e) {

      if (e.keyCode == 27){ // Escape key
          clearTimeout(keyDelay);
          $("#company-filter").val('');
          filter('');
      }
      else {

          var value = $(this).val().toLowerCase();

          delay(function() {
              filter(value);
          }, 500);
      }
  });

  $("#clear-filter").click(function(){
      clearTimeout(keyDelay);
      $("#company-filter").val('');
      filter('');
  });

  // Initially load the list with all values
  filter('');
});