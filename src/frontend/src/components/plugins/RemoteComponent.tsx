import { t } from '@lingui/core/macro';
import { Alert, Stack, Text } from '@mantine/core';
import { useRef } from 'react';

import { Boundary } from '@lib/components/Boundary';
import { identifierString } from '@lib/functions/Conversion';
import type { InvenTreePluginContext } from '@lib/types/Plugins';
import { IconExclamationCircle } from '@tabler/icons-react';
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

  const { componentFn, errorMsg, exportName, pluginContext, remountKey } =
    useRemotePlugin({
      context,
      source,
      defaultFunctionName,
      containerRef
    });

  const content = componentFn ? (
    componentFn(pluginContext)
  ) : (
    <div ref={containerRef} />
  );

  return (
    <Stack>
      {errorMsg && (
        <Alert
          color='red'
          title={t`Error Loading Plugin Content`}
          icon={<IconExclamationCircle />}
        >
          <Text>{errorMsg}</Text>
        </Alert>
      )}
      <Boundary
        key={remountKey}
        label={identifierString(`RemoteComponent-${exportName}`)}
      >
        {content}
      </Boundary>
    </Stack>
  );
}
