import { t } from '@lingui/macro';
import { Alert, Stack, Text } from '@mantine/core';
import { IconExclamationCircle } from '@tabler/icons-react';
import { ReactNode, useEffect, useRef, useState } from 'react';

import { InvenTreeContext } from './PluginContext';
import { findExternalPluginFunction } from './PluginSource';

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
  const ref = useRef<HTMLDivElement>();

  const [error, setError] = useState<string | undefined>(undefined);

  const reloadPluginContent = async () => {
    // If a "source" URL is provided, load the content from that URL
    if (pluginProps.source) {
      findExternalPluginFunction(pluginProps.source, 'renderPanel').then(
        (func) => {
          if (func) {
            try {
              func(ref.current, pluginContext);
              setError('');
            } catch (error) {
              setError(
                t`Error occurred while rendering plugin content` + `: ${error}`
              );
            }
          } else {
            setError(t`Plugin did not provide panel rendering function`);
          }
        }
      );
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
