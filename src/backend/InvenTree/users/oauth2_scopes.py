"""Static scope definitions for OAuth2 scopes."""


def get_granular_scope(method, role=None, type='r'):
    """Generate a granular scope string for a given method and role."""
    if role:
        return f'{type}:{method}:{role}'
    return f'{type}:{method}'


# region generated stuff
_roles = {
    'admin': 'Role Admin',
    'part_category': 'Role Part Categories',
    'part': 'Role Parts',
    'stocktake': 'Role Stocktake',
    'stock_location': 'Role Stock Locations',
    'stock': 'Role Stock Items',
    'build': 'Role Build Orders',
    'purchase_order': 'Role Purchase Orders',
    'sales_order': 'Role Sales Orders',
    'return_order': 'Role Return Orders',
}
_methods = {'view': 'GET', 'add': 'POST', 'change': 'PUT / PATCH', 'delete': 'DELETE'}

calculated = {
    get_granular_scope(method[0], role[0]): f'{method[1]} for {role[1]}'
    for method in _methods.items()
    for role in _roles.items()
}
# endregion


DEFAULT_READ = get_granular_scope('read', type='g')
DEFAULT_STAFF = get_granular_scope('staff', type='a')
DEFAULT_SUPERUSER = get_granular_scope('superuser', type='a')
# This is actually used
oauth2_scopes = {
    DEFAULT_READ: 'General Read scope',
    'openid': 'OpenID Connect scope',
    # Admin scopes
    DEFAULT_STAFF: 'User Role Staff',
    DEFAULT_SUPERUSER: 'User Role Superuser',
} | calculated
