{% load i18n %}
{% load inventree_extras %}
function loadBasketsTable(table, options) {

  options.params = options.params || {};
  // options.params['customer_detail'] = true;

  var filters = loadTableFilters('baskets');

  for (var key in options.params) {
      filters[key] = options.params[key];
  }

  options.url = options.url || '{% url "api-basket-list" %}';

  setupFilterList('baskets', $(table));

  $(table).inventreeTable({
      url: options.url,
      queryParams: filters,
      name: 'basket',
      groupBy: false,
      sidePagination: 'server',
      original: options.params,
      formatNoMatches: function() {
          return '{% trans "No baskets found" %}';
      },
      columns: [
          {
              title: '',
              checkbox: true,
              visible: true,
              switchable: false,
          },
          {
              sortable: true,
              field: 'name',
              title: '{% trans "Basket" %}',
              formatter: function(value, row) {


                  var html = renderLink(value, `/basket/${row.pk}/`);

                  if (row.status === 'busy') {
                      html += makeIconBadge('fa-calendar-times icon-red', '{% trans "Basket is busy" %}');
                  }

                  return html;
              },
          },
          {
              sortable: true,
              field: 'creation_date',
              title: '{% trans "Creation Date" %}',
          },
          {
              sortable: true,
              field: 'status',
              title: '{% trans "Status" %}',
              formatter: function(value, row) {
                  return salesOrderStatusDisplay(row.status, row.status_text);
              }
          },
      ],
  });
}