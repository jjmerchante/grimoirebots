$(document).ready(function(){
    // Configure ajax for using the CSRF token
    var csrftoken = getCookie('csrftoken');
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
    var dash_id = window.location.pathname.split('/')[2];
    getLogs(dash_id);
    getStatus(dash_id);
});


function getLogs(dash_id) {
    $.getJSON('/dashboard-logs/' + dash_id, function (data) {
        if (data && data.exists) {
            $('.log-content').html('');
            $('.log-content').html(data.content);
            if (data.more) {
                setTimeout(getLogs, 2000, dash_id);
            }
        } else {
            $('.log-content').html('Task not found or an error ocurred, try to reload the page.');
        }        
    });
}


function getStatus(dash_id) {
    // If the status is PENDING or RUNNING check the status every 2 seconds and reload when the status changes
    // Else: Nothing
    var initial_status = $('#initial-status').html();

    $.getJSON('/dashboard-status/' + dash_id, function (data) {
        if (!data || !data.status.exists) {
            console.log('Dashboard not found /dashboard/' + dash_id);
        } else {
            for (var i = 0; i < data.status.repos.length; i++){
                var repo = data.status.repos[i];
                if ($('#repo-' + repo.id + "-status").html() != repo.status){
                    $('#repo-' + repo.id + "-status").html(repo.status)
                }
            }
            if (data.status.general != 'PENDING' && data.status.general != initial_status) {
                location.reload()
            }
            if (data.status.general == 'PENDING' || data.status.general == 'RUNNING') {
                setTimeout(getStatus, 3000, dash_id);
            }
        }
    });
}


// Django function to adquire a cookie
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
