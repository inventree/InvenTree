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
              field: 'reference',
              title: '{% trans "Sales Order" %}',
              formatter: function(value, row) {

                  var prefix = global_settings.SALESORDER_REFERENCE_PREFIX;

                  if (prefix) {
                      value = `${prefix}${value}`;
                  }

                  var html = renderLink(value, `/order/basket/${row.pk}/`);

                  if (row.overdue) {
                      html += makeIconBadge('fa-calendar-times icon-red', '{% trans "Basket is busy" %}');
                  }

                  return html;
              },
          },
          {
              sortable: true,
              sortName: 'basket__name',
              field: 'customer_detail',
              title: '{% trans "Customer" %}',
              formatter: function(value, row) {

                  if (!row.customer_detail) {
                      return '{% trans "Invalid Basket" %}';
                  }

                  return imageHoverIcon(row.customer_detail.image) + renderLink(row.customer_detail.name, `/company/${row.customer}/sales-orders/`);
              }
          },
          {
              sortable: true,
              field: 'basket_name',
              title: '{% trans "Basket Name" %}',
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