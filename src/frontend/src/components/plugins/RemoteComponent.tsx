import { t } from '@lingui/core/macro';
import { Alert, Text } from '@mantine/core';
import { useRef } from 'react';

import { Boundary } from '@lib/components/Boundary';
import { identifierString } from '@lib/functions/Conversion';
import type { InvenTreePluginContext } from '@lib/types/Plugins';
import { IconExclamationCircle } from '@tabler/icons-react';
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

  const { componentFn, errorMsg, exportName, pluginContext, remountKey } =
    useRemotePlugin({
      context,
      source,
      defaultFunctionName,
      containerRef
    });

  return componentFn ? (
    <Boundary label={identifierString(`RemoteComponent-${exportName}`)}>
      <LanguageContext key={remountKey}>
        {componentFn(pluginContext)}
      </LanguageContext>
    </Boundary>
  ) : errorMsg ? (
    <Alert
      color='red'
      title={t`Error Loading Plugin Content`}
      icon={<IconExclamationCircle />}
    >
      <Text>{errorMsg}</Text>
    </Alert>
  ) : (
    <Boundary label={identifierString(`RemoteComponent-${exportName}`)}>
      <div ref={containerRef} />
    </Boundary>
  );
}
