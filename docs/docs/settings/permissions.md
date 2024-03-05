---
title: User Permissions
---

## Permissions

InvenTree provides access control to various features and data, by assigning each *user* to one (or more) *groups* which have multiple *roles* assigned.

!!! info "Superuser"
    The superuser account is afforded *all* permissions across an InvenTree installation. This includes the admin interface, web interface, and API.

### User

A *user* is a single unique account with login credentials. By default, a user is not afforded *any* permissions, and the user must be assigned to the relevant group for the permissions to be assigned.

### Group

A *group* is a named set of zero or more users. Each group is assigned permissions against each possible role.

### Role

A *role* is a set of distinct permissions linked to a given subset of InvenTree functionality (more on this below).

## Roles

InvenTree functionality is split into a number of distinct roles. A group will have a set of permissions assigned to each of the following roles:

- **Admin** - The *admin* role is related to assigning user permissions.
- **Part Category** - The *part category* role is related to accessing Part Category data
- **Part** - The *part* role is related to accessing Part data
- **Stock Location** - The *stock location* role is related to accessing Stock Location data
- **Stock Item** - The *stock item* role is related to accessing Stock Item data
- **Build** - The *build* role is related to accessing Build Order and Bill of Materials data
- **Purchase Order** - The *purchase* role is related to accessing Purchase Order data
- **Sales Order** - The *sales* role is related to accessing Sales Order data
- **Return Order** - The *return* role is related to accessing Return Order data

{% with id="Roles Admin View", url="admin/roles.png", description="Roles" %}
{% include 'img.html' %}
{% endwith %}

### Role Permissions

Within each role, there are four levels of available permissions:

- **View** - The *view* permission allows viewing of content related to the particular role
- **Change** - The *change* permission allows the user to edit / alter / change data associated with the particular role
- **Add** - The *add* permission allows the user to add / create database records associated with the particular role
- **Delete** - The *delete* permission allows the user to delete / remove database records associated with the particular role

## Admin Interface Permissions

If a user does not have the required permissions to perform a certain action in the admin interface, those options not be displayed.

If a user is expecting a certain option to be available in the admin interface, but it is not present, it is most likely the case that the user does not have those permissions assigned.

## Web Interface Permissions

When using the InvenTree web interface, certain functions may not be available for a given user, depending on their permissions. In this case, user-interface elements may be disabled, or may be removed.

## API Permissions

When using the InvenTree API, certain endpoints or actions may be inaccessible for a given user, depending on their permissions.

As the API is used extensively within the web interface, this means that many data tables may also be impacted by user permissions.
