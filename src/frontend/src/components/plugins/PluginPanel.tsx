import { t } from '@lingui/macro';
import { Alert, Stack, Text } from '@mantine/core';
import { IconExclamationCircle } from '@tabler/icons-react';
import { ReactNode, useEffect, useRef, useState } from 'react';

import { InvenTreeContext } from './PluginContext';
import { findExternalPluginFunction } from './PluginSource';
import RemoteComponent from './RemoteComponent';

// Definition of the plugin panel properties, provided by the server API
export type PluginPanelProps = {
  plugin: string;
  name: string;
  label: string;
  icon?: string;
  content?: string;
  context?: any;
  source?: string;
};

export async function isPluginPanelHidden({
  pluginProps,
  pluginContext
}: {
  pluginProps: PluginPanelProps;
  pluginContext: InvenTreeContext;
}): Promise<boolean> {
  if (!pluginProps.source) {
    // No custom source supplied - panel is not hidden
    return false;
  }

  const func = await findExternalPluginFunction(
    pluginProps.source,
    'isPanelHidden'
  );

  if (!func) {
    return false;
  }

  try {
    return func(pluginContext);
  } catch (error) {
    console.error(
      'Error occurred while checking if plugin panel is hidden:',
      error
    );
    return true;
  }
}

/**
 * A custom panel which can be used to display plugin content.
 *
 * - Content is loaded dynamically (via the API) when a page is first loaded
 * - Content can be provided from an external javascript module, or with raw HTML
 *
 * If content is provided from an external source, it is expected to define a function `render_panel` which will render the content.
 * const render_panel = (element: HTMLElement, params: any) => {...}
 *
 * Where:
 *  - `element` is the HTML element to render the content into
 *  - `params` is the set of run-time parameters to pass to the content rendering function
 */
export default function PluginPanelContent({
  pluginProps,
  pluginContext
}: Readonly<{
  pluginProps: PluginPanelProps;
  pluginContext: InvenTreeContext;
}>): ReactNode {
  // Div for rendering raw content for the panel (if provided)
  const pluginContentRef = useRef<HTMLDivElement>();

  useEffect(() => {
    if (pluginProps.content && pluginContentRef.current) {
      pluginContentRef.current?.setHTMLUnsafe(pluginProps.content.toString());
    }
  }, [pluginProps.content, pluginContentRef]);

  return (
    <Stack gap="xs">
      {pluginProps.content && <div ref={pluginContentRef as any}></div>}
      {pluginProps.source && (
        <RemoteComponent
          source={pluginProps.source}
          funcName="renderPanel"
          context={pluginContext}
        />
      )}
    </Stack>
  );
}
