/*
 * Expose shared modules as window globals for use in external plugins.
 *
 * This is loaded on demand (see ensurePluginGlobals in ./pluginGlobals) rather than at startup:
 * the namespace imports below defeat tree-shaking, so keeping them out of the
 * initial bundle avoids shipping all of @mantine/core to the login page.
 */
import * as LinguiCore from '@lingui/core';
import * as LinguiReact from '@lingui/react';
import * as MantineCore from '@mantine/core';
import * as MantineNotifications from '@mantine/notifications';
import * as React from 'react';
import * as ReactDOM from 'react-dom';
import * as ReactDOMClient from 'react-dom/client';

window.React = React;
window.ReactDOM = ReactDOM;
window.ReactDOMClient = ReactDOMClient;
window.MantineCore = MantineCore;
window.MantineNotifications = MantineNotifications;
window.LinguiCore = LinguiCore;
window.LinguiReact = LinguiReact;
