/**
 * Expose certain globals to the window object, so that they can be accessed by plugins,
 * without requiring plugins to import these dependencies directly.
 */
export function loadWindowGlobals() {
  // (window as any).React = React;
  import('react').then((module) => {
    window.React = module;
  });

  // (window as any).ReactDOM = ReactDOM;
  import('react-dom').then((module) => {
    window.ReactDOM = module;
  });

  // (window as any).ReactDOMClient = ReactDOMClient;
  import('react-dom/client').then((module) => {
    window.ReactDOMClient = module;
  });

  // (window as any).MantineCore = MantineCore;
  import('@mantine/core').then((module) => {
    window.MantineCore = module;
  });

  // (window as any).MantineNotifications = MantineNotifications;
  import('@mantine/notifications').then((module) => {
    window.MantineNotifications = module;
  });

  import('@lingui/core').then((module) => {
    window.LinguiCore = module;
  });

  import('@lingui/react').then((module) => {
    window.LinguiReact = module;
  });
}
