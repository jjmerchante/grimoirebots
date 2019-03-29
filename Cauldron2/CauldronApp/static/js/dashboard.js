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
        if (data && data.exists && data.ready) {
            $('.log-content').html('');
            $('.log-content').html(data.content);
            if (data.more) {
                setTimeout(getLogs, 1000, dash_id);
            }
        } else if(data && data.exists && !data.ready){ 
            $('.log-content').html('Logs not ready... Retrying');
            setTimeout(getLogs, 1000, dash_id);
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
        if (!data) {
            console.log('Bad response from server in /dashboard-status/' + dash_id);
        } else {
            console.log('Status: ' + data.status);
            if (data.status == 'PENDING' || data.status == 'RUNNING') {
                setTimeout(getStatus, 2000, dash_id);
            }
            if (data.status != initial_status) {
                console.log('The status has changed: initial' + initial_status + '. Now: ' + data.status);
                window.location.reload();
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
