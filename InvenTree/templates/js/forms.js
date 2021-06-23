/**
 * This file contains code for rendering (and managing) HTML forms
 * which are served via the django-drf API.
 * 
 * The django DRF library provides an OPTIONS method for each API endpoint,
 * which allows us to introspect the available fields at any given endpoint.
 * 
 * The OPTIONS method provides the following information for each available field:
 * 
 * - Field name
 * - Field label (translated)
 * - Field help text (translated)
 * - Field type
 * - Read / write status
 * - Field required status
 * - min_value / max_value 
 */

/*
 * Return true if the OPTIONS specify that the user
 * can perform a GET method at the endpoint.
 */
function canView(OPTIONS) {
    
    if ('actions' in OPTIONS) {
        return ('GET' in OPTIONS.actions);
    } else {
        return false;
    }
}


/*
 * Return true if the OPTIONS specify that the user
 * can perform a POST method at the endpoint
 */
function canCreate(OPTIONS) {

    if ('actions' in OPTIONS) {
        return ('POST' in OPTIONS.actions);
    } else {
        return false;
    }
}


/*
 * Return true if the OPTIONS specify that the user
 * can perform a PUT or PATCH method at the endpoint
 */
function canChange(OPTIONS) {
    
    if ('actions' in OPTIONS) {
        return ('PUT' in OPTIONS.actions || 'PATCH' in OPTIONS.actions);
    } else {
        return false;
    }
}


/*
 * Return true if the OPTIONS specify that the user
 * can perform a DELETE method at the endpoint
 */
function canDelete(OPTIONS) {

    if ('actions' in OPTIONS) {
        return ('DELETE' in OPTIONS.actions);
    } else {
        return false;
    }
}


/*
 * Get the API endpoint options at the provided URL,
 * using a HTTP options request.
 */
function getApiEndpointOptions(url, callback, options={}) {

    // Return the ajax request object
    $.ajax({
        url: url,
        type: 'OPTIONS',
        contentType: 'application/json',
        dataType: 'json',
        accepts: {
            json: 'application/json',
        },
        success: callback,
    });
}


/*
 * Request API OPTIONS data from the server,
 * and construct a modal form based on the response.
 * 
 * arguments:
 * - method: The HTTP method e.g. 'PUT', 'POST', 'DELETE',
 * 
 * options:
 * - method:
 */
function constructForm(url, method, options={}) {

    method = method.toUpperCase();

    // Request OPTIONS endpoint from the API
    getApiEndpointOptions(url, function(OPTIONS) {

        /*
         * Determine what "type" of form we want to construct,
         * based on the requested action.
         * 
         * First we must determine if the user has the correct permissions!
         */

        switch (method) {
            case 'POST':
                if (canCreate(OPTIONS)) {
                    console.log('create');
                } else {
                    // User does not have permission to POST to the endpoint
                    console.log('cannot POST');
                    // TODO
                }
                break;
            case 'PUT':
            case 'PATCH':
                if (canChange(OPTIONS)) {
                    console.log("change");
                } else {
                    // User does not have permission to PUT/PATCH to the endpoint
                    // TODO
                    console.log('cannot edit');
                }
                break;
            case 'DELETE':
                if (canDelete(OPTIONS)) {
                    console.log('delete');
                } else {
                    // User does not have permission to DELETE to the endpoint
                    // TODO
                    console.log('cannot delete');
                }
                break;
            case 'GET':
                if (canView(OPTIONS)) {
                    console.log('view');
                } else {
                    // User does not have permission to GET to the endpoint
                    // TODO
                    console.log('cannot view');
                }
                break;
            default:
                console.log(`constructForm() called with invalid method '${method}'`);
                break;
        }
    });
}