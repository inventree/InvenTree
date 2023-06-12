{% load i18n %}
{% load inventree_extras %}

/* globals
    Chart,
*/

/* exported
    loadBarChart,
    loadDoughnutChart,
    loadLineChart,
    randomColor,
*/


/* Generate a random color */
function randomColor() {
    return '#' + (Math.random().toString(16) + '0000000').slice(2, 8);
}


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
 * Load a simple doughnut chart
 */
function loadDoughnutChart(context, data) {
    return new Chart(context, {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
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
