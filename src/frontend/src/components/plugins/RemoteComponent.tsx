import { t } from '@lingui/macro';
import { Alert, Stack, Text } from '@mantine/core';
import { IconExclamationCircle } from '@tabler/icons-react';
import { useEffect, useMemo, useRef, useState } from 'react';

import { identifierString } from '../../functions/conversion';
import { Boundary } from '../Boundary';
import type { InvenTreeContext } from './PluginContext';
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
  context: InvenTreeContext;
}>) {
  const componentRef = useRef<HTMLDivElement>();

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

  const reloadPluginContent = async () => {
    if (!componentRef.current) {
      return;
    }

    if (sourceFile && functionName) {
      findExternalPluginFunction(sourceFile, functionName)
        .then((func) => {
          if (func) {
            try {
              func(componentRef.current, context);
              setRenderingError('');
            } catch (error) {
              setRenderingError(`${error}`);
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
  };

  // Reload the plugin content dynamically
  useEffect(() => {
    reloadPluginContent();
  }, [sourceFile, functionName, context]);

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
        <div ref={componentRef as any} />
      </Stack>
    </Boundary>
  );
}
