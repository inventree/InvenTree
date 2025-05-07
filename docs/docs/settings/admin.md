---
title: InvenTree Admin Interfaces
---

There are multiple administration interfaces available in InvenTree, which provide different levels of access to the underlying resources and different operational safety.

- Admin Center - Main interface for managing InvenTree - Robust verification and safety checks
- System Settings - Access to all settings - Robust verification, requires reading the documentation
- Backend Admin Interface - Low level access to the database - Few verification or safety checks

### Admin Center

The Admin Center is the main interface for managing InvenTree. It provides a user-friendly interface for managing all aspects of the system, including:
- Users / Groups
- Data import / export
- Customisation (e.g. project codes, custom states, parameters and units)
- Operational controls (e.g. background tasks, errors, currencies)
- Integration with external services (via machines and plugins)
- Reporting and statistics

It can be access via the *Admin Center* link in the top right user menu, the *Admin Center* quick-link in the command palette, or via the navigation menu.

#### Permissions

Some panes can only be accessed by users with specific permissions. For example, the *Stocktake* pane can only be accessed by users with the `stocktake` permission.

### System Settings

The System Settings interface provides ordered access to all global settings in InvenTree. Users need to have _staff_ privileges enabled or the _a:staff_ scope.

### Backend Admin Interface

Users which have *staff* privileges have access to an Admin interface which provides extremely low level control of the database. Every item in the database is available and this interface provides a unrestricted option for directly viewing and modifying database objects.

!!! warning "Caution"
	Admin users should exercise extreme care when modifying data via the admin interface, as performing the wrong action may have unintended consequences!

The admin interface allows *staff* users the ability to directly view / add / edit / delete database entries according to their [user permissions](./permissions.md).

#### Access Backend Admin Interface

To access the admin interface, select the "Admin" option from the drop-down user menu in the top-right corner of the screen.


!!! info "Staff Only"
    Only users with staff access will be able to see the "Admin" option

An administration panel will be presented as shown below:

{% with id="admin", url="admin/admin.png", description="InvenTree Admin Panel" %}
{% include 'img.html' %}
{% endwith %}

!!! info "Admin URL"
    To directly access the admin interface, append /admin/ to the InvenTree site URL - e.g. http://localhost:8000/admin/

#### View Database Objects

Database objects can be listed and filtered directly. The image below shows an example of displaying existing part categories.

{% with id="part_cats", url="admin/part_cats.png", description="Display part categories" %}
{% include 'img.html' %}
{% endwith %}

!!! info "Permissions"
    A "staff" account does not necessarily provide access to all administration options, depending on the roles assigned to the user.

##### Filtering

Some admin views support filtering of results against specified criteria. For example, the list of Part objects can be filtered as follows:

{% with id="filter", url="admin/filter.png", description="Filter part list" %}
{% include 'img.html' %}
{% endwith %}

#### Edit Database Objects

Individual database objects can be edited directly in the admin interface. The image below shows an example of editing a Part object:

{% with id="edit_part", url="admin/edit_part.png", description="Edit Part object" %}
{% include 'img.html' %}
{% endwith %}
