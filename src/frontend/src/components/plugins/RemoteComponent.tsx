import { t } from '@lingui/core/macro';
import { Alert, MantineProvider, Stack, Text } from '@mantine/core';
import { IconExclamationCircle } from '@tabler/icons-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { identifierString } from '@lib/functions/Conversion';
import type { InvenTreePluginContext } from '@lib/types/Plugins';
import { type Root, createRoot } from 'react-dom/client';
import { api, queryClient } from '../../App';
import { ApiProvider } from '../../contexts/ApiContext';
import { LanguageContext } from '../../contexts/LanguageContext';
import { useLocalState } from '../../states/LocalState';
import { Boundary } from '../Boundary';
import { findExternalPluginFunction } from './PluginSource';

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
  const componentRef = useRef<HTMLDivElement>();
  const rootElement = useRef<Root | null>(null);

  useEffect(() => {
    if (componentRef.current && rootElement.current === null) {
      rootElement.current = createRoot(componentRef.current);
    }
  }, [rootElement]);

  const [renderingError, setRenderingError] = useState<string | undefined>(
    undefined
  );

  const func: string = useMemo(() => {
    // Attempt to extract the function name from the source
    const { getHost } = useLocalState.getState();
    const url = new URL(source, getHost());

    if (url.pathname.includes(':')) {
      const parts = url.pathname.split(':');
      return parts[1] || defaultFunctionName; // Use the second part as the function name, or fallback to default
    } else {
      return defaultFunctionName;
    }
  }, [source, defaultFunctionName]);

  const reloadPluginContent = useCallback(() => {
    if (!rootElement.current) {
      return;
    }

    const ctx: InvenTreePluginContext = {
      ...context,
      reloadContent: reloadPluginContent
    };

    if (source && defaultFunctionName) {
      findExternalPluginFunction(source, func)
        .then((func) => {
          if (!!func) {
            try {
              if (func.length > 1) {
                // Support "legacy" plugin functions which call createRoot() internally
                // Ref: https://github.com/inventree/InvenTree/pull/9439/
                func(componentRef.current, ctx);
              } else {
                // Render the plugin component into the target element
                // Note that we have to provide the right context(s) to the component
                // This approach ensures that the component is rendered in the correct context tree
                rootElement.current?.render(
                  <ApiProvider client={queryClient} api={api}>
                    <MantineProvider
                      theme={ctx.theme}
                      defaultColorScheme={ctx.colorScheme}
                    >
                      <LanguageContext>{func(ctx)}</LanguageContext>
                    </MantineProvider>
                  </ApiProvider>
                );
              }

              setRenderingError('');
            } catch (error) {
              setRenderingError(`${error}`);
              console.error(error);
            }
          } else {
            setRenderingError(`${source} / ${func}`);
          }
        })
        .catch((_error) => {
          console.error(
            `ERR: Failed to load remote plugin function: ${source} /${func}`
          );
        });
    } else {
      setRenderingError(
        `${t`Invalid source or function name`} - ${source} /${func}`
      );
    }
  }, [
    componentRef.current,
    rootElement.current,
    source,
    defaultFunctionName,
    context
  ]);

  // Reload the plugin content dynamically
  useEffect(() => {
    reloadPluginContent();
  }, [
    func,
    rootElement.current,
    context.id,
    context.model,
    context.instance,
    context.user,
    context.colorScheme,
    context.locale,
    context.context
  ]);

  return (
    <Boundary label={identifierString(`RemoteComponent-${func}`)}>
      <Stack gap='xs'>
        {renderingError && (
          <Alert
            color='red'
            title={t`Error Loading Content`}
            icon={<IconExclamationCircle />}
          >
            <Text>
              {t`Error occurred while loading plugin content`}: {renderingError}
            </Text>
          </Alert>
        )}
        {componentRef && <div ref={componentRef as any} />}
      </Stack>
    </Boundary>
  );
}
