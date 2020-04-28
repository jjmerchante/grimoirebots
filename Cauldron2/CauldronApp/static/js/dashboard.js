var LogsInterval;
var BackendFilter = 'any';
var StatusFilter = 'all';
var TimeoutInfo = null; // To avoid multiple getInfo calls with timeouts
var Dash_ID = window.location.pathname.split('/')[2];

$(document).ready(function(){
    $('#logModal').on('show.bs.modal', onShowLogsModal);
    $('#logModal').on('hidden.bs.modal', OnHideLogsModal);
    $('form#gh_add').submit(submitBackend);
    $('form#gl_add').submit(submitBackend);
    $('form#meetup_add').submit(submitBackend);
    $('form#git_add').submit(submitBackend);

    $('.btn-delete').click(deleteRepo);
    $('.btn-reanalyze').click(reanalyzeRepo);
    $('.btn-reanalyze-all').click(reanalyzeEveryRepo);

    $('.btn-refresh-table').click(getInfo);

    //$('.backend-filters a').click(onFilterClick);
    //$('.status-filters a').click(onFilterClick);

    $('#rename').click(onClickEditName);

    $('form#change-name').on('submit', onSubmitRename);

    $("input#url-public-link").click(function () {
       $(this).select();
    });

    $('input#url-public-link-kibana').click(function (ev) {
        ev.target.select()
    })

    $('#repos-table').on('draw.dt', function() {
      getInfo();
    });

    getInfo();
    getSummary();
});


function onFilterClick(ev) {
    ev.preventDefault();
    $('.backend-item').removeClass('active');
    $(this).addClass('active');
    var filterType = $(this).attr('data-filter-type');

    if(filterType == 'status'){
        StatusFilter = $(this).attr('data-filter');
    } else if (filterType == 'backend'){
        BackendFilter = $(this).attr('data-filter');
    }
    filterTable();
}

function filterTable() {
    var num_filtered = 0;
    $('table.repos-table tbody tr').each(function(i, elem){
        var statusOK = (StatusFilter == 'all' || $(elem).attr('data-status') == StatusFilter);
        var backendOK = (BackendFilter == 'any' || $(elem).attr('data-backend') == BackendFilter);
        if ( statusOK && backendOK ){
            $(elem).show();
            num_filtered += 1;
        } else {
            $(elem).hide();
        }
    })
    $('#num-repos-filter').html(num_filtered);
    $('#btn-filter-status').html(`status: ${StatusFilter}`);
    $('#btn-filter-backend').html(`backend: ${BackendFilter}`);
}

function onClickEditName(ev) {
    ev.preventDefault();
    var old_name = $('#dash-name').text();

    $('#dash-name-container').hide();
    $('#change-name').show();

    $('input#new-name').popover();
    $('input#new-name').focus();
    $('input#new-name').val(old_name);
}


function deleteRepo(event) {
    var button = $(event.currentTarget);
    var id_repo = button.attr('data-repo');
    var backend = $(`tr#repo-${id_repo}`).attr('data-backend');
    var url_repo = $(`tr#repo-${id_repo} td.repo-url`).html();

    var deleteBtn = $(this);
    deleteBtn.html(`<div class="spinner-border spinner-border-sm" role="status">
                    <span class="sr-only">Loading...</span>
                </div>`);

    $.post(url = window.location.pathname + "/edit",
           data = {'action': 'delete', 'backend': backend, 'data': id_repo})
        .done(function (data) {
            showToast('Deleted', `The repository <b>${url_repo}</b> was deleted from this dashboard`, 'fas fa-check-circle text-success', 1500);
            $(`tr#repo-${id_repo}`).remove();
            //filterTable();
        })
        .fail(function (data) {
            showToast('Failed', `${data.responseJSON['status']} ${data.status}: ${data.responseJSON['message']}`, 'fas fa-times-circle text-danger', ERROR_TIMEOUT_MS);
        })
        .always(function(){deleteBtn.html('Delete')})

}

function reanalyzeRepo(event){
    var button = $(event.currentTarget);
    var id_repo = button.attr('data-repo');
    var backend = $(`tr#repo-${id_repo}`).attr('data-backend');
    var url_repo = $(`tr#repo-${id_repo} td.repo-url`).html();

    var reanalyzeRepo = $(this);
    reanalyzeRepo.html(`<div class="spinner-border spinner-border-sm" role="status">
                            <span class="sr-only">Loading...</span>
                        </div>`);
    $.post(url = window.location.pathname + "/edit",
           data = {'action': 'reanalyze', 'backend': backend, 'data': id_repo})
        .done(function (data) {
            if (data['status'] == 'reanalyze'){
                showToast('Reanalyzing', `The repository <b>${url_repo}</b> has refreshed`, 'fas fa-check-circle text-success', 1500);
                getInfo();
            } else {
                showToast(data['status'],  `The repository <b>${url_repo}</b> can not be refreshed`, 'fas fa-times-circle text-danger', ERROR_TIMEOUT_MS);
            }
        })
        .fail(function (data) {
            showToast('Failed', `${data.responseJSON['status']} ${data.status}: ${data.responseJSON['message']}`, 'fas fa-times-circle text-danger', ERROR_TIMEOUT_MS);
        })
        .always(function(){reanalyzeRepo.html('<i class="fa fa-sync"></i> <small>Refresh</small>')})
}

function reanalyzeEveryRepo(event){
    var id_repo = 'all';
    var backend = 'all';

    var reanalyzeRepo = $(this);
    reanalyzeRepo.html(`<div class="spinner-border spinner-border-sm" role="status">
                            <span class="sr-only">Loading...</span>
                        </div>`);
    $.post(url = window.location.pathname + "/edit",
           data = {'action': 'reanalyze-all', 'backend': backend, 'data': id_repo})
        .done(function (data) {
            if (data['status'] == 'reanalyze'){
                showToast('Reanalyzing', `${data.message}`, 'fas fa-check-circle text-success', 3000);
                getInfo();
            } else {
                showToast(data['status'], "The repositories couldn't be refreshed", 'fas fa-times-circle text-danger', ERROR_TIMEOUT_MS);
            }
        })
        .fail(function (data) {
            showToast('Failed', `${data.responseJSON['status']} ${data.status}: ${data.responseJSON['message']}`, 'fas fa-times-circle text-danger', ERROR_TIMEOUT_MS);
        })
        .always(function(){reanalyzeRepo.html('<i class="fa fa-sync"></i> Refresh')})
}

function getSummary() {
    $.getJSON('/dashboard/' + Dash_ID + "/summary", function(data) {
        var status_output = "";
        var i = 0;
        for (var key in data.status){
            status_output += `${key}: ${data.status[key]}`;
            if(i < Object.keys(data.status).length - 1) {
              status_output += ` | `;
            }
            i++;
        }

        $('#num-repos-filter').html(data.total);
        $('#general-status').html(status_output)
    });
    setTimeout(getSummary, 5000, Dash_ID);
}

function onSubmitRename(ev) {
    ev.preventDefault();

    $('input#new-name').popover('dispose');

    var url = $(this).attr("action");
    var data = $(this).serialize();
    var name = $('#new-name').val();

    $.post(url=url, data=data)
    .done(function (result) {
        $('#dash-name').text(name);

        $('#dash-name-container').show();
        $('#change-name').hide();

        showToast('Name updated', `${result.message}`, 'fas fa-check-circle text-success', 5000);
    })
    .fail(function (data) {
        showToast('Failed', `${data.responseJSON['status']} ${data.status}: ${data.responseJSON['message']}`, 'fas fa-times-circle text-danger', ERROR_TIMEOUT_MS);
        $('#dash-name-container').show();
        $('#change-name').hide();
    })
}

function getInfo() {
    //TimeoutInfo = null; // To avoid multiple getInfo calls
    $.getJSON('/dashboard/' + Dash_ID + "/info", function(data) {
        var status_dict = {"completed": 0,
                           "pending": 0,
                           "running": 0,
                           "error": 0}
        if (!data || !data.exists){
            return
        }
        data.repos.forEach(function(repo){
            if (!(repo.status.toLowerCase() in status_dict)){
                status_dict[repo.status.toLowerCase()] = 1;
            } else {
                status_dict[repo.status.toLowerCase()]++;
            }
            setIconStatus('#repo-' + repo.id + ' .repo-status', repo.status);
            $('#repo-' + repo.id).attr('data-status', repo.status.toLowerCase());
            if (repo.completed){
                $('#repo-' + repo.id + " .repo-last-update").html(moment(repo.completed).fromNow());
            } else {
                $('#repo-' + repo.id + " .repo-last-update").html("Not completed");
            }
            var duration = get_duration(repo);
            $('#repo-' + repo.id + " .repo-duration").html(duration);

        });
        //$('#general-status').html(data.general);
        /*if ((data.general == 'PENDING' || data.general == 'RUNNING') && !TimeoutInfo) {
            TimeoutInfo = setTimeout(getInfo, 5000, Dash_ID);
        }*/
        /*var status_output = "<strong>general status</strong>: " + data.general.toLowerCase();
        for (var key in status_dict){
            if (status_dict.hasOwnProperty(key)) {
                status_output += ` | <strong>${key}</strong>: ${status_dict[key]}`;
            }
        }
        $('#general-status').html(status_output)*/
    });
    //filterTable();
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
            icon = '<div class="spinner-grow spinner-grow-sm text-primary" role="status"><span class="sr-only">...</span></div> Pending...';
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
        if (repo.status == 'PENDING'){
          return "Waiting token"
        }
        var start = moment(repo.started);
        var finish = "";
        if (repo.status == 'RUNNING'){
            finish = moment();
        } else {
            finish = moment(repo.completed);
        }
        var duration = moment.duration(finish.diff(start));
        var h = Math.floor(duration.asHours());
        var m = Math.floor(duration.asMinutes()) % 60;
        var s = Math.floor(duration.asSeconds()) % 60;
        output = `${pad(h, 2)}:${pad(m, 2)}:${pad(s, 2)}`
    } else {
        output = "Not started";
    }
    return output
}

function pad(num, size) {
    var s = num + "";
    while (s.length < size) s = "0" + s;
    return s;
}

/****************************
 *     LOGS FUNCTIONS       *
 ****************************/
function onShowLogsModal(event) {
    var button = $(event.relatedTarget);
    var id_repo = button.attr('data-repo');
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


/************************
 *    BACKEND SUBMIT    *
 ************************/
function submitBackend(event) {
    event.preventDefault()
    var addBtn = $(`#${event.target.id} button`);
    addBtn.html(`<div class="spinner-border spinner-border-sm" role="status">
                    <span class="sr-only">Loading...</span>
                </div>`);

    $.post(url = window.location.pathname + "/edit",
           data = $(this).serializeArray())
        .done(function (data) {onDataAdded(data, event.target)})
        .fail(function (data) {onDataFail(data, event.target)})
        .always(function(){addBtn.html('Add')})
}

function onDataAdded(data, target) {
    $(`#${target.id} input[type=text]`).val('');
    window.location.reload()
}

function onDataFail(data, target) {
    if(!data.hasOwnProperty('responseJSON')){
        showToast('Unknown error from server', `${data.responseText}`, 'fas fa-question-circle text-danger', ERROR_TIMEOUT_MS);
        return;
    }
    if (data.responseJSON.hasOwnProperty('redirect')){
        var redirect = `<a href="${data.responseJSON['redirect']}" class="btn btn-primary">Go</a>`;
        showModalAlert('Do you let us?', `<p class="text-justify">${data.responseJSON['message']}</p>`,  redirect);
    } else {
        showToast('Failed', `${data.responseJSON['status']} ${data.status}: ${data.responseJSON['message']}`, 'fas fa-times-circle text-danger', ERROR_TIMEOUT_MS);
    }
}
