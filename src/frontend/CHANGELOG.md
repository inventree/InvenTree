## InvenTree UI Components - Changelog

This file contains historical changelog information for the InvenTree UI components library.

### 1.0.0 - April 2025

Published the first version of the UI components API. This allows external plugins to hook into the InvenTree user interface, and provides global access to the following objects:

- `window.React`: The core `react` library running on the UI
- `window.ReactDOM`: The `react-dom` library
- `window.ReactDOMClient`: The `react-dom/client` library
- `window.MantineCore`: The `@mantine/core` library
- `window.MantineNotifications`: The `@mantine/notifications` library

All of these components can be "externalized" in the plugin build step.
