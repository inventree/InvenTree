import { t } from '@lingui/macro';
import { Alert, Loader, LoadingOverlay, Stack, Text } from '@mantine/core';
import { IconExclamationCircle } from '@tabler/icons-react';
import React, { ReactNode, useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';

import { PluginContext } from './PluginContext';
import { loadExternalPluginSource } from './PluginSource';

// Definition of the plugin panel properties, provided by the server API
export type PluginPanelProps = {
  plugin: string;
  name: string;
  label: string;
  icon?: string;
  content?: string;
  source?: string;
  render_function?: string;
  hidden_function?: string;
};

export function isPluginPanelHidden({
  pluginProps,
  pluginContext
}: {
  pluginProps: PluginPanelProps;
  pluginContext: PluginContext;
}): boolean {
  console.log('isPluginPanelHidden', pluginProps, pluginContext);

  return false;
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
}: {
  pluginProps: PluginPanelProps;
  pluginContext: PluginContext;
}): ReactNode {
  const ref = useRef<HTMLDivElement>();

  const [error, setError] = useState<string | undefined>(undefined);

  const reloadPluginContent = async () => {
    // If a "source" URL is provided, load the content from that URL
    if (pluginProps.source) {
      const renderFunc = pluginProps.render_function || 'renderPanel';

      loadExternalPluginSource(pluginProps.source).then((module) => {
        if (module && module[renderFunc]) {
          try {
            module[renderFunc]({
              ...pluginContext,
              target: ref.current
            });
            setError('');
          } catch (error) {
            setError(t`Error occurred while rendering plugin content`);
          }
        } else {
          if (!module) {
            setError(
              t`Failed to load plugin source` + ': ' + pluginProps.source
            );
          } else if (!module[renderFunc]) {
            setError(t`Failed to find render function`);
          } else {
            setError(t`Failed to render plugin content`);
          }
        }
      });
    } else if (pluginProps.content) {
      // If content is provided directly, render it into the panel
      if (ref.current) {
        ref.current?.setHTMLUnsafe(pluginProps.content.toString());
        setError('');
      }
    } else {
      // If no content is provided, display a placeholder
      setError(t`No content provided for this plugin`);
    }
  };

  useEffect(() => {
    reloadPluginContent();
  }, [pluginProps, pluginContext]);

  return (
    <Stack gap="xs">
      {error && (
        <Alert
          color="red"
          title={t`Error Loading Plugin`}
          icon={<IconExclamationCircle />}
        >
          <Text>{error}</Text>
        </Alert>
      )}
      <div ref={ref as any}></div>
    </Stack>
  );
}
