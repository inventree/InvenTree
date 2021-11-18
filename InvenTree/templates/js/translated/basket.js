{% load i18n %}
{% load inventree_extras %}


function loadBasketsTable(table, options) {

  options.params = options.params || {};
  // options.params['customer_detail'] = true;

  var filters = loadTableFilters('basket');

  for (var key in options.params) {
      filters[key] = options.params[key];
  }

  options.url = options.url || '{% url "api-basket-list" %}';

  setupFilterList('basket', $(table));

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

                  if (row.status === 10) {
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
                  return basketStatusDisplay(row.status, row.status_text);
              }
          },
      ],
  });
}


function createBasket(options={}) {

    constructForm('{% url "api-basket-list" %}', {
        method: 'POST',
        fields: {
            // reference: {
            //     prefix: global_settings.SALESORDER_REFERENCE_PREFIX,
            // },
            name: {},
            // status: {
            //     icon: 'fa-calendar-alt',
            // },
            // link: {
            //     icon: 'fa-link',
            // },
            // responsible: {
            //     icon: 'fa-user',
            // }
        },
        onSuccess: function(data) {
            location.href = `/order/sales-order/${data.pk}/`;
        },
        title: '{% trans "Create Basket" %}',
    });
}


/**
 * Load a table displaying orders for a particular Basket
 * 
 * @param {String} table : HTML ID tag e.g. '#table'
 * @param {Object} options : object which contains:
 *      - order {integer} : pk of the Basket
 *      - status: {integer} : status code for the Basket
 */
function loadBasketOrdersTable(table, options={}) {

    options.table = table;

    options.params = options.params || {};

    if (!options.basket) {
        console.log('ERROR: function called without basket ID');
        return;
    }

    if (!options.status) {
        console.log('ERROR: function called without basket status');
        return;
    }

    options.params.basket = options.basket;
    // options.params.part_detail = true;
    // options.params.allocations = true;
    
    var filters = loadTableFilters('salesorder');

    for (var key in options.params) {
        filters[key] = options.params[key];
    }

    options.url = options.url || '{% url "api-so-list" %}';

    var filter_target = options.filter_target || '#sales-order';

    setupFilterList('salesorder', $(table), filter_target);

}
