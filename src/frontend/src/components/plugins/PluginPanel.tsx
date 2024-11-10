import { Stack } from '@mantine/core';
import type { ReactNode } from 'react';

import type { InvenTreeContext } from './PluginContext';
import type { PluginUIFeature } from './PluginUIFeature';
import RemoteComponent from './RemoteComponent';

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
  pluginFeature,
  pluginContext
}: Readonly<{
  pluginFeature: PluginUIFeature;
  pluginContext: InvenTreeContext;
}>): ReactNode {
  return (
    <Stack gap='xs'>
      <RemoteComponent
        source={pluginFeature.source}
        defaultFunctionName='renderPanel'
        context={pluginContext}
      />
    </Stack>
  );
}
