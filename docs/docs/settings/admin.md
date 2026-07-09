---
title: InvenTree Admin Interfaces
---

## InvenTree Admin Interfaces

InvenTree provides multiple administration interfaces with different safety levels and intended use cases.

[**Admin Center**](#admin-center):

- Main administration interface for day-to-day operations
- Uses API-backed flows with validation and safety checks

[**System Settings**](#system-settings):

- Access to global runtime settings
- Available to staff users (or users with equivalent API scope)

[**Database Admin Interface**](./db_admin.md):

- Low-level database administration
- Fewer safeguards than the Admin Center
- Intended for advanced users and troubleshooting scenarios

### Admin Center

The Admin Center is the main interface for managing InvenTree. It provides a user-friendly interface for managing all aspects of the system, including:

- Users / Groups
- Data import / export
- Customisation (e.g. project codes, custom states, parameters and units)
- Operational controls (e.g. background tasks, errors, currencies)
- Integration with external services (via machines and plugins)
- Reporting and statistics

#### Access Admin Center

The Admin Center can be accessed in any of the following ways:

- User menu in the top-right corner: *Admin Center*
- Command palette quick action: *Admin Center*
- Direct URL: `/web/settings/admin`

!!! info "Screenshot Placeholder"
	TODO: Add screenshot of the Admin Center landing page (`/web/settings/admin`).

#### Permissions

Some panes can only be accessed by users with specific permissions. For example, the *Stocktake* pane can only be accessed by users with the `stocktake` permission.

### System Settings

The System Settings interface provides ordered access to all global settings in InvenTree. Users need to have _staff_ privileges enabled or the _a:staff_ scope.

### Database Admin Interface

For low-level administration tasks, use the [Database Admin Interface](./db_admin.md).
