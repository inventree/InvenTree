{% load i18n %}
{% load inventree_extras %}

/* globals
*/

/* exported
    loadBarChart,
    loadLineChart
*/

/*
 * Load a simple bar chart
 */
function loadBarChart(context, data) {
    return new Chart(context, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}


/*
 * Load a simple line chart
 */
function loadLineChart(context, data) {
    return new Chart(context, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {position: 'bottom'},
            }
        }
    });
}
