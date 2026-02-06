---
title: User Interface
---

## User Interface

The InvenTree user interface is designed to be intuitive and user-friendly, providing easy access to the various features and functions of the system. The interface is organized into several key components, including navigation menus, settings, forms, tables, search functionality, and more.

The interface is designed for large-format displays, and as such is explicitly *not* optimized for mobile devices. However, the interface is responsive and should work on a wide range of desktop screen sizes.

## Navigation

Navigation throughout the InvenTree interface is designed to be straightforward and efficient, allowing users to quickly access the various sections and features of the system. The navigation is organized into several key areas, including the main menu, navigation menu, and page panels.

### Main Menu

The main menu is located at the top of the interface and provides access to the primary sections of the system:

{{ image("concepts/ui_main_menu.png", "Main Menu") }}

From the main menu, users can access the following items:

- [Navigation Menu](#navigation-menu)
- [Dashboard](#dashboard)
- [Global Search](#search)
- [Spotlight](#spotlight)
- [Barcode Scanning](#barcode-scanning)
- [Notifications](#notifications)
- [User Menu](#user-menu)

As well as allowing navigation to the following main sections:

- [Parts](../parts/index.md)
- [Stock](../stock/index.md)
- [Manufacturing](../manufacturing/index.md)
- [Purchasing](../purchasing/index.md)
- [Sales](../sales/index.md)

### Navigation Menu

The global navigation menu is located on the left-hand side of the interface and provides access to the various sections of the system.

{{ image("concepts/ui_navigation_menu.png", "Navigation Menu") }}

The navigation menu is organized into several key areas, including:

- **Navigation:** Provides access to the main sections of the system, including Parts, Stock, Manufacturing, Purchasing, and Sales.
- **Settings:** Quick access to user settings, system settings, and the admin interface.
- **Actions:** Provides quick access to commonly used actions
- **Documentation:** Links to the online documentation.
- **About:** InvenTree version and license information.

### User Menu

The user menu is located in the top-right corner of the interface and provides access to user-specific settings and actions.

{{ image("concepts/ui_user_menu.png", "User Menu") }}

The user menu provides access to the following items:

- **User Settings:** Access to [user-specific](../settings/user.md) settings, such as profile information and preferences.
- **System Settings:** Access to [system-wide](../settings/system.md) settings, such as configuration options and system information. *Note: Access to system settings may be restricted based on user permissions.*
- **Admin Interface:** Access to the [admin interface](../settings/admin.md) for data management. *Note: Access to the admin interface may be restricted based on user permissions.*
- **Change Color Mode:** Toggle between light and dark color modes.
- **About InvenTree:** View version and license information about InvenTree.
- **Logout:** Log out of the InvenTree system.

### Page Panels

Most detail pages views within InvenTree are organized into panels, which provide a structured layout for displaying information and actions related to the current page.

Panels are arranged in a vertical stack on the left side of the page, with the main content area on the right. Each panel contains related information and actions, allowing users to easily navigate and interact with the content.

{{ image("concepts/ui_panels.png", "Page Panels") }}

### Breadcrumbs

On some pages, a breadcrumb navigation trail is provided at the top of the page, just below the main menu. Breadcrumbs provide a visual representation of the user's current location within the system and allow for easy navigation back to previous pages.

{{ image("concepts/ui_breadcrumbs.png", "Breadcrumb Navigation") }}

### Navigation Tree

On some pages, a navigation tree is provided on the left-hand side of the page, next to the breadcrumbs. The navigation tree provides a hierarchical view of the current section of the system, allowing users to quickly navigate to related pages and sections.

Click on the navigation tree icon to expand the tree and view the available navigation options:

{{ image("concepts/ui_navigation_tree.png", "Navigation Tree") }}

## Dashboard

The dashboard provides a customizable landing page for users when they log in to the system. The dashboard can be configured to display a variety of widgets and information panels, providing users with quick access to important data and actions.

{{ image("concepts/ui_dashboard.png", "Dashboard") }}

### Editing Layout

To edit the layout (add, remove, or rearrange widgets) of the dashboard, open the dashboard context menu (located at the top-right corner of the dashboard) and view the available options:

{{ image("concepts/ui_dashboard_edit.png", "Dashboard Context Menu") }}

### Custom Widgets

In addition to the set of built-in widgets provided by InvenTree, custom dashboard widgets can be implemented using [plugins](../plugins/mixins/ui.md#dashboard-items). This allows users to create personalized dashboard experiences tailored to their specific needs and workflows.

## Settings

### User Settings

### System Settings

### Admin Interface

## Forms

## Tables

### Filtering

### Searching

### Data Download

### Row Actions

## Global Search

## Spotlight

## Barcode Scanning

## Notifications

## Customization

## User Permissions
