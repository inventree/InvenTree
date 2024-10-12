import { t } from '@lingui/macro';
import { Alert, Stack, Text } from '@mantine/core';
import { IconExclamationCircle } from '@tabler/icons-react';
import { useEffect, useRef, useState } from 'react';

import { Boundary } from '../Boundary';
import { InvenTreeContext } from './PluginContext';
import { findExternalPluginFunction } from './PluginSource';

/**
 * A remote component which can be used to display plugin content.
 * Content is loaded dynamically (from an external source).
 */
export default function RemoteComponent({
  source,
  funcName,
  context
}: {
  source: string;
  funcName: string;
  context: InvenTreeContext;
}) {
  const componentRef = useRef<HTMLDivElement>();
  const [renderingError, setRenderingError] = useState<string | undefined>(
    undefined
  );

  const reloadPluginContent = async () => {
    if (!componentRef.current) {
      return;
    }

    if (source && funcName) {
      findExternalPluginFunction(source, funcName).then((func) => {
        if (func) {
          try {
            func(componentRef.current, context);
            setRenderingError('');
          } catch (error) {
            setRenderingError(`${error}`);
          }
        } else {
          setRenderingError(`${source}.${funcName}`);
        }
      });
    }
  };

  // Reload the plugin content dynamically
  useEffect(() => {
    reloadPluginContent();
  }, [source, funcName, context]);

  return (
    <>
      <Boundary label={`RemoteComponent-${source}-${funcName}`}>
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
