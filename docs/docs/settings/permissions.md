---
title: User Permissions
---

## Permissions

InvenTree provides access control to various features and data, by assigning each *user* to one (or more) *groups* which have multiple *roles* assigned.

!!! info "Superuser"
    The superuser account is afforded *all* permissions across an InvenTree installation. This includes the [Database Admin interface](./db_admin.md), web interface, and API.

### User

A *user* is a single unique account with login credentials. By default, a user is not afforded *any* permissions, and the user must be assigned to the relevant group for the permissions to be assigned.

### Group

A *group* is a named set of zero or more users. Each group is assigned permissions against each possible role.

### Role

A *role* is a set of distinct permissions linked to a given subset of InvenTree functionality (more on this below).

## Roles

InvenTree functionality is split into a number of distinct roles. A group will have a set of permissions assigned to each of the following roles:

{{ roles() }}

!!! info "Pricing Role"
    Access to part pricing data is controlled separately from general part data, via the *Pricing* role. Refer to the [pricing permissions](../part/pricing.md#pricing-permissions) documentation for more information.

{{ image("admin/roles.png", "Roles") }}

### Role Permissions

Within each role, there are four levels of available permissions:

| Permission | Description |
| ---------- | ----------- |
| **View** | The *view* permission allows viewing of content related to the particular role |
| **Change** | The *change* permission allows the user to edit / alter / change data associated with the particular role |
| **Add** | The *add* permission allows the user to add / create database records associated with the particular role |
| **Delete** | The *delete* permission allows the user to delete / remove database records associated with the particular role |

### Implied Permissions

Some permissions automatically imply other permissions within the same role:

- The *add* and *delete* permissions imply the *change* permission
- Any permission (*add*, *change* or *delete*) implies the *view* permission

For example, if a group is assigned the *add* permission for the *Stock Items* role, the *change* and *view* permissions are also assigned. It is not possible to assign the *add* permission without the *change* permission.

## Role Models

Each role grants permissions against a particular set of database models:

{{ role_models() }}

### Shared Models

Some models are associated with more than one role. A user who has a particular permission via *any* of these roles is granted that permission for the model:

{{ shared_role_models() }}

!!! warning "Roles grant access to shared models"
    Take care when assigning roles which share models with other roles. For example, the *Build Orders* role grants access to parts, BOM items, stock items and stock locations - so a user with the *add* permission for *Build Orders* can also create and edit stock items via the API, even if they do not have any permissions for the *Stock Items* role.

!!! info "OAuth2 scopes for shared models"
    When accessing the API via an [OAuth2 token](../api/index.md#scopes), the API endpoints for a shared model require the token to hold the scopes for **all** of the roles associated with that model - not just one of them.

## Dangerous User Flags

In addition to the above permissions, there are two special flags that can be assigned to a user:
- **Staff** - A user with the *staff* flag is able to access the [Database Admin interface](./db_admin.md), and can trigger dangerous actions that might have a security impact such as changing parsable files on the server (templates / reports / plugins). Some of these actions require the *admin* role to be assigned as well.
- **Superuser** - A user with the *superuser* flag is able to access and change all data and functions of InvenTree. A superuser can modify and access all data that the InvenTree installation / server has access to - including shell access on the server OS itself. This is a very powerful flag, and should be used with caution.

It is strongly recommended to register any users with staff / superuser flags with strong MFA methods to reduce the risk of unauthorized access. These accounts should be used with caution, and should not be used for day-to-day operations.

Practicing account tiering is strongly recommended.


## Database Admin Permissions

If a user does not have the required permissions to perform a certain action in the [Database Admin interface](./db_admin.md), those options will not be displayed.

If a user is expecting a certain option to be available in the Database Admin interface, but it is not present, it is most likely the case that the user does not have those permissions assigned.

## Web Interface Permissions

When using the InvenTree web interface, certain functions may not be available for a given user, depending on their permissions. In this case, user-interface elements may be disabled, or may be removed.

## API Permissions

When using the InvenTree API, certain endpoints or actions may be inaccessible for a given user, depending on their permissions.

As the API is used extensively within the web interface, this means that many data tables may also be impacted by user permissions.

Most API endpoints require the permission (for the role associated with the endpoint's data) which matches the type of request - e.g. *view* permission to read data, *add* permission to create new data.

Some "action" endpoints require a specific role permission, as they modify data which is associated with a different role than the endpoint itself. For example:

| Action | Required Permissions |
| --- | --- |
| Stock adjustments (count, add, remove, transfer, return, change status, assign to customer, merge) | *Stock Items* - change |
| Copy BOM from another part | *BOM* - add (and *BOM* - delete, if existing BOM items are removed) |
| Validate BOM | *BOM* - change |

!!! info "Additional permission checks"
    Some endpoints perform additional permission checks against the data which is affected by a request. For example, adding an attachment or parameter to a part requires the *change* permission for parts, and linking a barcode to a stock item requires the *change* permission for stock items.
