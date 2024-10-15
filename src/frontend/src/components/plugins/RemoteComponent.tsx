import { t } from '@lingui/macro';
import { Alert, Stack, Text } from '@mantine/core';
import { IconExclamationCircle } from '@tabler/icons-react';
import { useEffect, useMemo, useRef, useState } from 'react';

import { identifierString } from '../../functions/conversion';
import { Boundary } from '../Boundary';
import { InvenTreeContext } from './PluginContext';
import { findExternalPluginFunction } from './PluginSource';
import { PluginUIFeature } from './PluginUIFeature';

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
  pluginFeature,
  defaultFunctionName,
  context
}: {
  pluginFeature: PluginUIFeature;
  defaultFunctionName: string;
  context: InvenTreeContext;
}) {
  const componentRef = useRef<HTMLDivElement>();

  const [renderingError, setRenderingError] = useState<string | undefined>(
    undefined
  );

  const sourceFile = useMemo(() => {
    return pluginFeature.source.split(':')[0];
  }, [pluginFeature.source]);

  // Determine the function to call in the external plugin source
  const functionName = useMemo(() => {
    // The "source" string may contain a function name, e.g. "source.js:myFunction"
    if (pluginFeature.source.includes(':')) {
      return pluginFeature.source.split(':')[1];
    }

    // By default, return the default function name
    return defaultFunctionName;
  }, [pluginFeature.source, defaultFunctionName]);

  const reloadPluginContent = async () => {
    if (!componentRef.current) {
      return;
    }

    if (sourceFile && functionName) {
      findExternalPluginFunction(sourceFile, functionName).then((func) => {
        if (func) {
          try {
            func(componentRef.current, context);
            setRenderingError('');
          } catch (error) {
            setRenderingError(`${error}`);
          }
        } else {
          setRenderingError(`${sourceFile}.${functionName}`);
        }
      });
    } else {
      setRenderingError(
        t`Invalid source or function name` + ` : ${sourceFile}.${functionName}`
      );
    }
  };

  // Reload the plugin content dynamically
  useEffect(() => {
    reloadPluginContent();
  }, [sourceFile, functionName, context]);

  return (
    <>
      <Boundary
        label={identifierString(
          `RemoteComponent-${sourceFile}-${functionName}`
        )}
      >
        <Stack gap="xs">
          {renderingError && (
            <Alert
              color="red"
              title={t`Error Loading Content`}
              icon={<IconExclamationCircle />}
            >
              <Text>
                {t`Error occurred while loading plugin content`}:{' '}
                {renderingError}
              </Text>
            </Alert>
          )}
          <div ref={componentRef as any}></div>
        </Stack>
      </Boundary>
    </>
  );
}
