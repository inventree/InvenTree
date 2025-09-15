# InvenTree UI Components - Changelog

This file contains historical changelog information for the InvenTree UI components library.

### 0.5.0 - August 2025

This release updates the base `react` major version from `18.3.1` to `19.1.1`. This change may introduce breaking changes for plugins that rely on the InvenTree UI components library (plugin developers should test their plugins against this new version).

Ref: https://github.com/inventree/InvenTree/pull/10202/

### 0.4.0 - July 2025

Externalize React, Lingui and Mantine libraries in the plugin library build step to avoid version conflicts. This ensures that the components provided as part of the @inventreedb/ui package *does not bundle* the React and Mantine libraries, but instead expects them to be provided by the InvenTree server.

This change fixes issues with version mismatches between the InvenTree server and the plugin, allowing plugins to utilize the common components provided by the InvenTree UI components library without conflicts.

*Note: Without this change, the components introduced in `0.3.0` would not work correctly, as they are pre-compiled with a different React instance.*

### New Functions

Adds the following functions to the API:

- `initPlugin`: Initializes the plugin with the provided context

### New UI Components

- `AddItemButton`: A common button component used throughout the InvenTree UI

### New Types

Exposes a number of new internal types related to the API forms interface:

- ApiFormFieldChoice
- ApiFormFieldHeader
- ApiFormFieldType
- ApiFormFieldSet
- ApiFormProps
- ApiFormModalProps
- BulkEditApiFormModalProps


## 0.3.0 - July 2025

Introduces new types and functions to enhance the InvenTree UI components API.

### New Types

- `ModelDict`: A dictionary type for InvenTree models, allowing for easier access to model instances.

### New Functions

- `formatCurrencyValue`: A utility function to format currency values consistently across the UI.
- `formatDecimal`: A utility function to format decimal values, ensuring consistent display of numerical data.
- `formatFileSize`: A utility function to format file sizes, making it easier to read large numbers.

### New UI Components

- `ActionButton`: A button component build on the Mantine `<Button`> component.
- `ButtonMenu`: A menu component that provides a dropdown of icon actions.
- `PassFailButton`: A button component that can be used to indicate pass/fail states, useful for testing or validation scenarios.
- `YesNoButton`: A button component that provides a simple yes/no choice, useful for confirmation dialogs.
- `ProgressBar`: A progress bar component that can be used to indicate loading or processing states.
- `SearchInput`: An input component that provides a search functionality, allowing users to filter data easily.
- `RowViewAction`: A component that provides a row view action in a table.
- `RowDuplicateAction`: A component that provides a row duplicate action in a table.
- `RowEditAction`: A component that provides a row edit action in a table.
- `RowDeleteAction`: A component that provides a row delete action in a table.
- `RowCancelAction`: A component that provides a row cancel action in a table.
- `RowActions`: A component that provides a set of row actions in a table, allowing for multiple actions to be performed on a row.


## 0.2.0 - June 2025

- Bug fixes and performance improvements. No major changes introduced in this version.

## 0.1.0 - May 2025

Published the first version of the UI components API. This allows external plugins to hook into the InvenTree user interface, and provides global access to the following objects:

- `window.React`: The core `react` library running on the UI
- `window.ReactDOM`: The `react-dom` library
- `window.ReactDOMClient`: The `react-dom/client` library
- `window.MantineCore`: The `@mantine/core` library
- `window.MantineNotifications`: The `@mantine/notifications` library

All of these components can be "externalized" in the plugin build step.

### New Types

- `ApiEndpoints`: An object containing the API endpoints for the InvenTree server.
- `ModelType`: A type representing the available model types in InvenTree.
- `UserRoles`: An object containing the user roles available in InvenTree.
- `UserPermissions`: An object containing the user permissions available in InvenTree.
- `InvenTreePluginContext`: The context object for InvenTree plugins, providing access to the API and other utilities.

### New Functions

- `apiUrl`: Construct an API URL for the InvenTree server.
- `getBaseUrl`: Get the base URL for the InvenTree server.
- `getDetailUrl`: Get the detail URL for a specific model type.
- `navigateToLink`: Navigate to a provided link, either internal or external.
- `checkPluginVersion`: Check the version of a plugin against the InvenTree server.
