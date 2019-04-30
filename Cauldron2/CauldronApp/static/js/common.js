LocalStorageAvailable = false;

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
    LocalStorageAvailable = checkLocalStorage()
    loadLastLocation();
});


/**
 * Check if LocalStorage works in this browser
 */
function checkLocalStorage() {
    try {
        localStorage.setItem('test', 'test');
        localStorage.removeItem('test');
        return true;
    } catch(e) {
        return false;
    }
}

/**
 *   Django function to adquire a cookie
 */
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


/**
 * Check if the method is safe. These methods don't require CSRF protection
 */
function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}


/**
 * Show an alert in the top of the page
 * Possible options for style: primary, secondary, success, danger, warning, info, light and dark
 * Styles: https://getbootstrap.com/docs/4.0/components/alerts/
 */
function showAlert(title, message, style) {
    $('#alert-container').hide();
    var alertMessage = `<div class="alert alert-${style}" role="alert">
                            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                            </button>
                            <h4 class="alert-heading">${title}</h4>
                            <p>${message}</p>
                        </div>`
    $('#alert-container').html(alertMessage);
    $('#alert-container').show();
}

/**
 * Show a modal with the title and the message passed
 */
function showModalAlert(title, message) {
    $('#modal-alert').modal('hide');
    $('#modal-alert h5').html(title);
    $('#modal-alert p').html(message);
    $('#modal-alert').modal('show');
}

/**
 * Load the last location. This trick is for redirect after GitHub or Gitlab oauth
 * It will not work if the browser doesn't accept localStorage
 */
function loadLastLocation() {
    if (!LocalStorageAvailable){
        return;
    }
    var location = window.localStorage.getItem('location');
    if (location){
        window.localStorage.removeItem('location');
        window.location.href = location;
    }
}