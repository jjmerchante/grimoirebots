var LogsInterval;

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
    getInfo(dash_id);
    $('#logModal').on('show.bs.modal', onShowLogsModal);
    $('#logModal').on('hidden.bs.modal', OnHideLogsModal);
});


function onShowLogsModal(event) {
    var button = $(event.relatedTarget);
    var id_repo = button.data('repo');
    if (LogsInterval) {
        clearInterval(LogsInterval);
        LogsInterval = null;
    }
    LogsInterval = setInterval(updateLogs, 1000, id_repo);
}

function OnHideLogsModal(event) {
    if(LogsInterval){
        clearInterval(LogsInterval);
        LogsInterval = null;
    }
    $('#logModal .log-content ').html('Loading...');
}

function updateLogs(id_repo){
    $.getJSON('/repo-logs/' + id_repo, function (data) {
        if (!data){
            $('#logModal .log-content').html('Task not found or an error occurred, try to reload the page.');
            if (LogsInterval){
                clearInterval(LogsInterval);
                LogsInterval = null;
            } 
            return // NOTHING MORE TO DO
        }
        if (data.content) {
            $('#logModal .log-content ').html('');
            $('#logModal .log-content ').html(data.content);
        }
        if (!data.more) {
            if (LogsInterval){
                clearInterval(LogsInterval);
                LogsInterval = null;
            }
        }
    });
}

function getInfo(dash_id) {
    $.getJSON('/dashboard-info/' + dash_id, function(data) {
        if (!data || !data.exists){
            return
        }
        data.repos.forEach(function(repo){
            setIconStatus('#repo-' + repo.id + ' .repo-status', repo.status);
            $('#repo-' + repo.id + " .repo-creation").html(moment(repo.created).fromNow());
            var duration = get_duration(repo);
            $('#repo-' + repo.id + " .repo-duration").html(duration);

        });
        $('#general-status').html(data.general);
        if (data.general == 'PENDING' || data.general == 'RUNNING') {
            setTimeout(getInfo, 5000, dash_id);
        }
    });
    
}


function setIconStatus(jq_selector, status) {
    /**
     * Status could be UNKNOWN, RUNNING, PENDING, COMPLETED OR ERROR
     */
    var icon;
    switch (status) {
        case 'COMPLETED':
            icon = '<i class="fas fa-check text-success"></i>';
            break;
        case 'PENDING':
            icon = '<div class="spinner-grow spinner-grow-sm text-primary" role="status"><span class="sr-only">...</span></div> Not started...';
            break;
        case 'RUNNING':
            icon = '<div class="spinner-border spinner-border-sm text-secondary" role="status"><span class="sr-only">...</span></div> Running...';
            break;
        case 'ERROR':
            icon = '<i class="fas fa-exclamation text-warning"></i> Error.';
            break;
        case 'UNKNOWN':
            icon = '<i class="fas fa-question text-warning"></i>';
            break;
        default:
            break;
    }
    $(jq_selector).html(icon);
}


function get_duration(repo) {
    var output = "";
    if (repo.started){
        var a = moment(repo.started);
        var b = "";
        if (repo.completed){
            b = moment(repo.completed);
        } else {
            b = moment();
        }
        output = moment.utc(b.diff(a)).format("HH:mm:ss")
    } else {
        output = "Not started";
    }
    return output
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
