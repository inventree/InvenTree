import { MantineProvider } from '@mantine/core';
import { useRef } from 'react';

import type { InvenTreePluginContext } from '@lib/types/Plugins';
import { api, queryClient } from '../../App';
import { ApiProvider } from '../../contexts/ApiContext';
import { LanguageContext } from '../../contexts/LanguageContext';
import { useRemotePlugin } from '../../hooks/UseRemotePlugin';

/**
 * A remote component which can be used to display plugin content.
 * Content is loaded dynamically (from an external source).
 *
 * @param pluginFeature: The plugin feature to render
 * @param defaultFunctionName: The default function name to call (if not overridden by pluginFeature.source)
 * @param pluginContext: The context to pass to the plugin function
 *
 */
export default function RemoteComponent({
  source,
  defaultFunctionName,
  context
}: Readonly<{
  source: string;
  defaultFunctionName: string;
  context: InvenTreePluginContext;
}>) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  const componentFn = useRemotePlugin({context, source, defaultFunctionName, containerRef});

  return componentFn ? (
    <ApiProvider client={queryClient} api={api}>
      <MantineProvider
        theme={context.theme}
        defaultColorScheme={context.colorScheme}
      >
        <LanguageContext>
          {componentFn(context)}
        </LanguageContext>
      </MantineProvider>
    </ApiProvider>
  ) : (
    <div ref={containerRef} />
  );
}
