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

- [Parts](../part/index.md)
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

- **User Settings:** Access to [user settings](../settings/user.md).
- **System Settings:** Access to [global settings](../settings/global.md) settings. *Note: Access to system settings may be restricted based on user permissions.*
- **Admin Interface:** Access to the [admin interface](../settings/admin.md) for data management. *Note: Access to the admin interface may be restricted based on user permissions.*
- **Change Color Mode:** Toggle between light and dark color modes.
- **About InvenTree:** View version and license information about InvenTree.
- **Logout:** Log out of the InvenTree system.

### Page Panels

Most detail pages views within InvenTree are organized into panels, which provide a structured layout for displaying information and actions related to the current page.

Panels are arranged in a vertical stack on the left side of the page, with the main content area on the right. Each panel contains related information and actions, allowing users to easily navigate and interact with the content.

{{ image("concepts/ui_panels.png", "Page Panels") }}

#### Collapse Panels

The panel sidebar can be collapsed to provide more space for the main content area. To collapse or expand the panel sidebar, click the collapse icon located at the bottom of the sidebar. To expand the sidebar again, click the expand icon that appears when the sidebar is collapsed.

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

## Table Views

Information throughout the InvenTree interface is often presented in tabular format, allowing users to easily view and interact with large datasets. Tables are designed to be flexible and customizable, providing a range of features to enhance the user experience.

{{ image("concepts/ui_table.png", "Table View") }}

### Pagination

The pagination controls are located at the bottom of the table, allowing users to navigate through large datasets by moving between pages. Users can also adjust the number of rows displayed per page using the pagination settings.

### Row Selection

For tables where data selection is supported, a checkbox is provided at the left-hand side of each row, allowing users to select one or more rows for further actions. A master checkbox is also provided in the table header, allowing users to quickly select or deselect all rows in the table.

!!! info "Pagination and Row Selection"
    When using the "master select" checkbox to select all rows, only the rows on the current page will be selected.

{{ image("concepts/ui_table_row_selection.png", "Row Selection") }}

### Table Actions

A particular table view may have a set of actions associated with it, which are typically located at the top-left corner of the table. These actions may include options for adding new entries, or performing bulk actions on [selected rows](#row-selection).

{{ image("concepts/ui_table_actions.png", "Table Actions") }}

### Searching

Some tables support searching, allowing users to quickly find specific entries within the dataset. The search bar is  located at the top-right corner of the table view:

{{ image("concepts/ui_table_search.png", "Table Search") }}

### Column Selection

Some tables allow the user to toggle the visibility of certain columns to, enabling a more customized view of the data.

Column selection is accessed via the "Select Columns" menu, located to the top-right of the table view:

{{ image("concepts/ui_table_column_selection.png", "Column Selection") }}

### Filtering

The dataset (which is fetched dynamically from the server via an API request) can be filtered by providing query parameters to the API endpoint.

Select the "table filters" button to open the filter selection menu

{{ image("concepts/ui_table_filter_button.png", "Table Filter Button") }}

{{ image("concepts/ui_table_filter_menu.png", "Table Filter Menu") }}

Table filters are saved across browser sessions, allowing users to maintain their preferred filter settings when returning to the particular table view.

### Data Sorting

Some table columns support data sorting, allowing the dataset to be sorted in ascending or descending order based on the values in that column. To sort a column, click on the column header. Clicking the column header again will toggle the sort order between ascending and descending. The current sort order is indicated by an arrow icon in the column header.

{{ image("concepts/ui_table_sorting.png", "Data Sorting") }}

### Data Export

Some tables support downloading of the dataset in various formats (e.g. CSV, Excel, PDF). If data download is available for a given table, the "export data" button will be located at the top-right corner of the table view.

This opens the "Export Data" form, which allows the user to select the desired file format for download, as well as any additional options related to the data export.

{{ image("concepts/ui_table_download.png", "Data Download") }}

### Row Actions

In some tables, there may be specific actions associated with individual rows, allowing users to perform actions directly on a particular entry in the dataset. Row actions are typically accessed via an "actions" menu located at the right-hand side of each row.

{{ image("concepts/ui_table_row_actions.png", "Row Actions") }}

### Right-Click Context Menu

For rows that support row actions, a right-click context menu is also available, providing quick access to the same set of actions without needing to click on the "actions" menu.

{{ image("concepts/ui_table_context_menu.png", "Right-Click Context Menu") }}

### Row Navigation

For tables which reference other objects within the system, clicking on a row will navigate to the detail page for that particular entry. For example, clicking on a row in the "Part" table will navigate to the detail page for that specific part.

## Calendar Views

Some [table views](#table-views) can be switched to a calendar view, which provides a visual representation of data based on date fields. The calendar view allows users to easily see and interact with data that is organized by date, such as scheduled tasks, events, or deadlines.

To switch to the "calendar view" (for a table which supports it), click on the "calendar view" button located above and to the right of the table view:

{{ image("concepts/ui_calendar_select.png", "Calendar View Button") }}

This will display the data in a calendar format:

{{ image("concepts/ui_calendar_view.png", "Calendar View") }}

## Parametric Views

Some [table views](#table-views) can be switched to a parametric view, which provides a visual representation of data based on specific parameters or attributes. The parametric view allows users to easily see and interact with data that is organized by certain characteristics, such as categories, types, or other relevant attributes.

To switch to the "parametric view" (for a table which supports it), click on the "parametric view" button located above and to the right of the table view:

{{ image("concepts/ui_parametric_select.png", "Parametric View Button") }}

This will display the data in a parametric format:

{{ image("concepts/ui_parametric_view.png", "Parametric View") }}

## Forms

Data entry and editing within InvenTree is typically performed through the use of forms, which provide a structured interface for inputting and modifying data. Forms are designed to be user-friendly and efficient, allowing users to quickly enter and update information within the system.

Forms are typically displayed as a modal dialog, separated into multiple sections and fields.

### Data Creation

Example: Creating a new part via the "Add Part" form:

{{ image("concepts/ui_form_add_part.png", "Add Part Button") }}

### Data Editing

Example: Editing an existing purchase order via the "Edit Purchase Order" form:

{{ image("concepts/ui_form_edit_po.png", "Edit Purchase Order") }}

### Confirm Actions

Many actions within InvenTree require user confirmation before they can be executed. This is typically implemented through the use of confirmation dialogs, which prompt the user to confirm their intention before proceeding with the action.

{{ image("concepts/ui_form_hold_po.png", "Confirmation Dialog") }}

## Global Search

Accessible from the [main menu](#main-menu), the global search functionality allows users to quickly find specific items or information within the InvenTree system. The search icon is located at the top of the interface and provides a convenient way to search across all sections of the system.

Clicking on the "search" icon (in the menu bar) opens the search menu, which allows users to enter search queries and view results from across the system.

{{ image("concepts/ui_global_search.png", "Global Search") }}

Search results are organized by category (e.g. Parts, Stock, Manufacturing, etc.) and provide quick access to the relevant pages for each search result.

### Detail View

To navigate to the detail page for a particular search result, simply click on the desired result from the search results list. This will take you directly to the relevant page within the InvenTree system, allowing you to view and interact with the specific item or information you were searching for.

### Full Results

The "global search" menu provides a limited set of search results for each category, typically showing the most relevant or recent results. To view the full set of search results for a particular category, click on the "View all results" button located at the top-left of the search results list for that category:

{{ image("concepts/ui_global_search_view_all.png", "View Full Search Results") }}

### Collapse Result Groups

To collapse a particular category of search results in the global search menu, click on the "collapse" icon located at the top-right corner of the search results list for that category. This will hide the search results for that category, allowing you to focus on other categories or search results.

### Remove Result Groups

To remove a particular category of search results from the global search menu, click on the "remove" icon located at the top-right corner of the search results list for that category.

## Spotlight

The user interface features a "spotlight" search functionality, which provides a quick and efficient way to access common actions or navigate to specific pages within the InvenTree system. The spotlight search is designed to enhance user productivity by allowing users to quickly find and execute actions without needing to navigate through menus or remember specific page locations.

{{ image("concepts/ui_spotlight.png", "Spotlight Search") }}

### Open Spotlight

To open the "spotlight" search, click on the "spotlight" icon located in the main menu at the top of the interface. This will open the spotlight search menu, allowing you to enter search queries and view available actions.

Alternatively, the spotlight search can be opened using the keyboard shortcut `Ctrl + K` (or `Cmd + K` on macOS), providing a quick and convenient way to access the spotlight functionality without needing to click on the menu icon.

### Disable Spotlight

Users may opt to disable the spotlight search functionality if they do not find it useful or prefer not to use it. To disable the spotlight search, navigate to your [user settings](../settings/user.md) and locate the option to disable the spotlight feature. Once disabled, the spotlight search will no longer be accessible from the main menu or via keyboard shortcuts.

## Barcode Scanning

## Notifications

## Customization

## User Permissions

Many aspects of the user interface are controlled by user permissions, which determine what actions and features are available to each user based on their assigned roles and permissions within the system. This allows for a highly customizable user experience, where different users can have access to different features and functionality based on their specific needs and responsibilities within the organization.

If a user does not have permission to access a particular feature or section of the system, that feature will be hidden from their view in the user interface. This helps to ensure that users only see the features and information that are relevant to their role, reducing clutter and improving usability.
