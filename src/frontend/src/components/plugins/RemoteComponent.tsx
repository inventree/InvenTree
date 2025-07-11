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
  const [rootElement, setRootElement] = useState<Root | null>(null);

  useEffect(() => {
    if (componentRef.current && !rootElement) {
      setRootElement(createRoot(componentRef.current));
    }
  }, [componentRef.current]);

  const [renderingError, setRenderingError] = useState<string | undefined>(
    undefined
  );

  const sourceFile = useMemo(() => {
    return source.split(':')[0];
  }, [source]);

  // Determine the function to call in the external plugin source
  const functionName = useMemo(() => {
    // The "source" string may contain a function name, e.g. "source.js:myFunction"
    if (source.includes(':')) {
      return source.split(':')[1];
    }

    // By default, return the default function name
    return defaultFunctionName;
  }, [source, defaultFunctionName]);

  const reloadPluginContent = useCallback(() => {
    if (!rootElement) {
      return;
    }

    const ctx: InvenTreePluginContext = {
      ...context,
      reloadContent: reloadPluginContent
    };

    if (sourceFile && functionName) {
      findExternalPluginFunction(sourceFile, functionName)
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
                rootElement.render(
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
            setRenderingError(`${sourceFile}:${functionName}`);
          }
        })
        .catch((_error) => {
          console.error(
            `ERR: Failed to load remove plugin function: ${sourceFile}:${functionName}`
          );
        });
    } else {
      setRenderingError(
        `${t`Invalid source or function name`} - ${sourceFile}:${functionName}`
      );
    }
  }, [componentRef, rootElement, sourceFile, functionName, context]);

  // Reload the plugin content dynamically
  useEffect(() => {
    reloadPluginContent();
  }, [sourceFile, functionName, context, rootElement]);

  return (
    <Boundary
      label={identifierString(`RemoteComponent-${sourceFile}-${functionName}`)}
    >
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
