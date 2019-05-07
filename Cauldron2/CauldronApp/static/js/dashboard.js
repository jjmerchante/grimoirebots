var LogsInterval;

$(document).ready(function(){
    var dash_id = window.location.pathname.split('/')[2];
    getInfo(dash_id);
    $('#logModal').on('show.bs.modal', onShowLogsModal);
    $('#logModal').on('hidden.bs.modal', OnHideLogsModal);
    loadLastStatus();
    $('form#gh_url_add').submit(submitURL);
    $('form#gh_owner_add').submit(submitOwner);
    $('form#gl_url_add').submit(submitURL);
    $('form#gl_owner_add').submit(submitOwner);

    $('.btn-delete').click(deleteRepo);

    loadCallbackFilters();
});

function loadLastStatus(){
    if(!LocalStorageAvailable){
        return
    }
    var gh_owner = window.localStorage.getItem('gh_owner');
    var gh_url = window.localStorage.getItem('gh_url');
    var gl_owner = window.localStorage.getItem('gl_owner');
    var gl_url = window.localStorage.getItem('gl_url');
    window.localStorage.removeItem('gh_owner');
    window.localStorage.removeItem('gh_url');
    window.localStorage.removeItem('gl_owner');
    window.localStorage.removeItem('gl_url');
    $('#gh_owner').val(gh_owner);
    $('#gh_url').val(gh_url);
    $('#gl_owner').val(gl_owner);
    $('#gl_url').val(gl_url);
}

function loadCallbackFilters(){
    $('button#option-all').click(function () {
        $('tr[data-backend=git]').show();
        $('tr[data-backend=gitlab]').show();
        $('tr[data-backend=github]').show();
    });

    $('button#option-github').click(function () {
        $('tr[data-backend=git]').hide();
        $('tr[data-backend=gitlab]').hide();
        $('tr[data-backend=github]').show();
    });

    $('button#option-git').click(function () {
        $('tr[data-backend=git]').show();
        $('tr[data-backend=gitlab]').hide();
        $('tr[data-backend=github]').hide();
    });

    $('button#option-gitlab').click(function () {
        $('tr[data-backend=git]').hide();
        $('tr[data-backend=gitlab]').show();
        $('tr[data-backend=github]').hide();
    });
}

function deleteRepo(event) {
    var id_repo = event.target.dataset['repo'];
    var backend = $(`tr#repo-${id_repo}`).data('backend');
    var url_repo = $(`tr#repo-${id_repo} td.repo-url`).html();

    var deleteBtn = $(this);
    deleteBtn.html(`<div class="spinner-border text-dark spinner-border-sm" role="status">
                    <span class="sr-only">Loading...</span>
                </div>`);


    $.post(url = window.location.pathname + "/edit", 
           data = {'action': 'delete', 'backend': backend, 'url': url_repo})
        .done(function (data) {
            showToast('Deleted', `The repository <b>${url_repo}</b> was deleted from this dashboard`, 'fas fa-check-circle text-success', 5000);
            $(`tr#repo-${id_repo}`).remove();
        })
        .fail(function (data) {
            showToast('Failed', `${data.responseJSON['status']} ${data.status}: ${data.responseJSON['message']}`, 'fas fa-times-circle text-danger', 5000);
        })
        .always(function(){deleteBtn.html('Delete')})

    
}

function getInfo(dash_id) {
    $.getJSON('/dashboard-info/' + dash_id, function(data) {
        if (!data || !data.exists){
            return
        }
        updateBadgesRepos(data.repos);
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

function updateBadgesRepos(repo_arr) {
    var repos_gh = 0;
    var repos_gl = 0;
    var repos_git = 0;
    repo_arr.forEach(function(repo){
        if (repo.backend == 'github'){
            repos_gh += 1;
        } else if (repo.backend == 'gitlab'){
            repos_gl += 1;
        } else if (repo.backend == 'git'){
            repos_git += 1;
        }        
    });
    $('.badge-repos-all').html(repos_git + repos_gh + repos_gl)
    $('.badge-repos-gh').html(repos_gh)
    $('.badge-repos-gl').html(repos_gl)
    $('.badge-repos-git').html(repos_git)
}


/****************************
 *     LOGS FUNCTIONS       *
 ****************************/
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



/****************************
 *     GITHUB GITLAB URL    *
 ****************************/
function submitURL(event) {
    var addBtn = $(`#${event.target.id} button`);
    addBtn.html(`<div class="spinner-border text-dark spinner-border-sm" role="status">
                    <span class="sr-only">Loading...</span>
                </div>`);
    
    $.post(url = window.location.pathname + "/edit", 
           data = $(this).serializeArray())
        .done(function (data) {onURLAdded(data, event.target)})
        .fail(function (data) {onURLFail(data, event.target)})
        .always(function(){addBtn.html('Add')})
    event.preventDefault()
}

function onURLAdded(data, target) {
    showToast('Success', `URL added correctly. Reloading the list of repositories...`, 'fas fa-spinner text-success', 5000);
    setTimeout(function(){window.location.reload()}, 2000);
}

function onURLFail(data, target) {
    if(!data.hasOwnProperty('responseJSON')){
        showToast('Unknown error from server', `${data.responseText}`, 'fas fa-question-circle text-danger', 5000);
        return;
    }
    if (data.responseJSON.hasOwnProperty('redirect')){
        if(LocalStorageAvailable){
            var input_target = $(`#${target.id} input[name=url]`);
            window.localStorage.setItem('location', window.location.href);
            window.localStorage.setItem(input_target.attr('id'), input_target.val());
        }
        var a_redirect = `<a href="${data.responseJSON['redirect']}" class="btn btn-primary"> Go</a>`;
        showModalAlert('We can not add it right now...', `<p><b>${data.responseJSON['message']}</b></p>`,  a_redirect);
    } else {
        showToast('Failed', `${data.responseJSON['status']} ${data.status}: ${data.responseJSON['message']}`, 'fas fa-times-circle text-danger', 5000);
    }
}

/******************************
 *     GITHUB GITLAB OWNER    *
 ******************************/
function submitOwner(event) {
    var addBtn = $(`#${event.target.id} button`);
    addBtn.html(`<div class="spinner-border text-dark spinner-border-sm" role="status">
                    <span class="sr-only">Loading...</span>
                </div>`);

    $.post(url = window.location.pathname + "/edit", 
           data = $(this).serializeArray())
        .done(function (data) {onOwnerAdded(data, event.target)})
        .fail(function (data) {onOwnerFail(data, event.target)})
        .always(function () {addBtn.html('Add');})
        event.preventDefault()
}

function onOwnerAdded(data, target) {
    showToast('Success', `User/organization added correctly. Reloading the list of repositories...`, 'fas fa-spinner text-success', 5000);
    setTimeout(function(){window.location.reload()}, 2000);
}

function onOwnerFail(data, target) {
    if(!data.hasOwnProperty('responseJSON')){
        showToast('Unknown error from server', `${data.responseText}`, 'fas fa-question-circle text-danger', 5000);
        return;
    }
    if (data.responseJSON.hasOwnProperty('redirect')){
        var input_target = $(`#${target.id} input[name=owner]`);
        if(LocalStorageAvailable){
            window.localStorage.setItem('location', window.location.href);
            window.localStorage.setItem(input_target.attr('id'), input_target.val());
        }

        var a_redirect = `<a href="${data.responseJSON['redirect']}" class="btn btn-primary"> Go</a>`;
        showModalAlert('We can not add it right now...', `<p><b>${data.responseJSON['message']}</b></p>`,  a_redirect);
        setTimeout(function(){window.location.href = data.responseJSON['redirect']}, 5000);
    } else {
        showToast('Failed', `${data.responseJSON['status']} ${data.status}: ${data.responseJSON['message']}`, 'fas fa-times-circle text-danger', 5000);
    }
}
