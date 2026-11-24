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

## Dangerous User Flags

In addition to the above permissions, there are two special flags that can be assigned to a user:
- **Staff** - A user with the *staff* flag is able to access the [Database Admin interface](./db_admin.md), and can trigger dangerous actions that might have a security impact such as changing parsable files on the server (templates / reports / plugins). Some of these actions require the *admin* role to be assigned as well.
- **Superuser** - A user with the *superuser* flag is able to access and change all data and functions of InvenTree. A superuser can modify and access all data that the InvenTree installation / server has access to - including shell access on the server OS itself. This is a very powerful flag, and should be used with caution.

It is strongly recommended to register any users with staff / superuser flags with strong MFA methods to reduce the risk of unauthorized access. These accounts should be used with caution, and should not be used for day-to-day operations.

Practicing account tiering is strongly recommended.

## Managing Users and Groups

Users and groups are managed from the *Users / Access* panel of the [Admin Center](./admin.md#admin-center).

!!! info "Required Permissions"
    Creating and editing users and groups requires the *staff* flag **and** the relevant permissions for the *Admin* role. Users without these permissions can view the users and groups, but cannot make any changes.

### Users

The *Users* table lists all user accounts, along with the number of groups each user belongs to and their *Administrator*, *Superuser* and *Active* flags. Use the {{ icon("plus", color="green") }} button to create a new user.

{{ image("settings/admin_users_table.png", "Users table") }}

Click on a user to open the *Edit User* drawer.

#### User Details

The *User Details* section allows the user's name and account flags to be edited.

{{ image("settings/admin_edit_user.png", "Edit user details") }}

!!! tip "Deactivate Users"
    Rather than deleting a user account, consider unchecking the *Is Active* flag. This prevents the user from logging in, while retaining the history of their actions.

#### User Groups

The *User Groups* section shows which groups the user belongs to. Move groups between the *Available* and *Selected* lists, then press *Save* to update the user's group memberships.

{{ image("settings/admin_user_groups.png", "Edit user groups") }}

### Groups

The *Groups* table lists all user groups. Use the {{ icon("plus", color="green") }} button to create a new group.

{{ image("settings/admin_groups_table.png", "Groups table") }}

Click on a group to open the *Edit Group* drawer.

#### Group Details

The *Group Details* section allows the name of the group to be changed.

{{ image("settings/admin_edit_group.png", "Edit group details") }}

#### Group Roles

The *Group Roles* section sets the [role permissions](#role-permissions) for every user in the group. Check the required *View*, *Change*, *Add* and *Delete* permissions for each role, then press *Save*.

{{ image("settings/admin_group_roles.png", "Edit group roles") }}

#### Group Users

The *Group Users* section lists the users who belong to the group. From here, users can be quickly added to or removed from the group:

- **Add a user** - search for the user in the *Add User* field and select them. The user is added to the group immediately.
- **Remove a user** - press the {{ icon("user-minus", color="red") }} button next to the user.

These changes only affect membership of this group - the user's other group memberships are not changed.

{{ image("settings/admin_group_users.png", "Edit group users") }}

!!! info "Permissions"
    Adding or removing users from a group edits the *user* account, so it requires *change* permission for users (as well as the *staff* flag). If you do not have this permission, the list of users is displayed in read-only mode.


## Database Admin Permissions

If a user does not have the required permissions to perform a certain action in the [Database Admin interface](./db_admin.md), those options will not be displayed.

If a user is expecting a certain option to be available in the Database Admin interface, but it is not present, it is most likely the case that the user does not have those permissions assigned.

## Web Interface Permissions

When using the InvenTree web interface, certain functions may not be available for a given user, depending on their permissions. In this case, user-interface elements may be disabled, or may be removed.

## API Permissions

When using the InvenTree API, certain endpoints or actions may be inaccessible for a given user, depending on their permissions.

As the API is used extensively within the web interface, this means that many data tables may also be impacted by user permissions.
