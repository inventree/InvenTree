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
 * Get the API endpoint options at the provided URL,
 * using a HTTP options request.
 */
function getApiEndpointOptions(url, options={}) {

    // Return the ajax request object
    return $.ajax({
        url: url,
        type: 'OPTIONS',
        contentType: 'application/json',
        dataType: 'json',
        accepts: {
            json: 'application/json',
        },
    });
}


