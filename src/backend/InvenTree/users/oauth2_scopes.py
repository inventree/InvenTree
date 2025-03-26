"""Static scope definitions for OAuth2 scopes."""

oauth2_scopes = {
    'read': 'Read scope',
    'write': 'Write scope',
    # user roles
    'superuser': 'Role Superuser',
    # inventree roles
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
    # inventree methods
    'view': 'Method GET',
    'create': 'Method POST',
    'change': 'Method PUT / PATCH',
    'delete': 'Method DELETE',
}
