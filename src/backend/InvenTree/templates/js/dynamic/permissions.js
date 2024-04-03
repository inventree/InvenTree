/*
 * globals
    inventreeGet,

/* exported
    checkPermission,
*/

// Keep track of the current user permissions
var user_roles = null;


/*
 * Check if the user has the specified role and permission
 */
function checkPermission(role, permission='view') {

    // Allow permission to be specified in dotted notation, e.g. 'part.add'
    if (role.indexOf('.') > 0) {
        let parts = role.split('.');
        role = parts[0];
        permission = parts[1];
    }

    // Request user roles if we do not have them
    if (user_roles == null) {
        inventreeGet('{% url "api-user-roles" %}', {}, {
            async: false,
            success: function(response) {
                user_roles = response.roles || {};
            }
        });
    }

    if (user_roles == null) {
        console.error("Failed to fetch user roles");
        return false;
    }

    if (!(role in user_roles)) {
        return false;
    }

    let roles = user_roles[role];

    if (!roles) {
        return false;
    }

    let found = false;

    user_roles[role].forEach(function(p) {
        if (String(p).valueOf() == String(permission).valueOf()) {
            found = true;
        }
    });

    return found;
}
