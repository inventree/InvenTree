function run_task(name, args, success_cb, failure_cb) {
    $.ajax({
        url: '/common/tasks/run/',
        data: $.extend({ name: 'common.tasks.debug_task' }, args),
        method: 'POST',
        beforeSend: function(request) {
            request.setRequestHeader("X-CSRFToken", csrftoken);
        },
    })
    .done((res) => {
        success_cb(res);
    })
    .fail((err) => {
        failure_cb(err);
    });
}

function get_task_status(id,  success_cb, failure_cb) {
    $.ajax({
        url: '/common/tasks/'+id+'/',
        method: 'GET',
        beforeSend: function(request) {
            request.setRequestHeader("X-CSRFToken", csrftoken);
        },
    })
    .done((res) => {
        success_cb(res);
    })
    .fail((err) => {
        failure_cb(err);
    });
}
