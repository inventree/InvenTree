import { t } from '@lingui/macro';
import { Alert, Stack, Text } from '@mantine/core';
import { IconExclamationCircle } from '@tabler/icons-react';
import { useEffect, useMemo, useRef, useState } from 'react';

import { useInvenTreeContext } from './PluginContext';
import { findExternalPluginFunction } from './PluginSource';

/**
 * Interface for the plugin admin data
 */
export interface PluginAdminInterface {
  source: string;
  context: any;
}

/**
 * A panel which is used to display custom settings UI for a plugin.
 *
 * This settings panel is loaded dynamically,
 * and requires that the plugin provides a javascript module,
 * which exports a function `renderPluginSettings`
 */
export default function PluginSettingsPanel({
  pluginInstance,
  pluginAdmin
}: {
  pluginInstance: any;
  pluginAdmin: PluginAdminInterface;
}) {
  const ref = useRef<HTMLDivElement>();
  const [error, setError] = useState<string | undefined>(undefined);

  const pluginContext = useInvenTreeContext();

  const pluginSourceFile = useMemo(() => pluginAdmin?.source, [pluginInstance]);

  const loadPluginSettingsContent = async () => {
    if (pluginSourceFile) {
      findExternalPluginFunction(pluginSourceFile, 'renderPluginSettings').then(
        (func) => {
          if (func) {
            try {
              func(ref.current, {
                ...pluginContext,
                context: pluginAdmin.context
              });
              setError('');
            } catch (error) {
              setError(
                t`Error occurred while rendering plugin settings` + `: ${error}`
              );
            }
          } else {
            setError(t`Plugin did not provide settings rendering function`);
          }
        }
      );
    }
  };

  useEffect(() => {
    loadPluginSettingsContent();
  }, [pluginSourceFile]);

  if (!pluginSourceFile) {
    return null;
  }

  return (
    <>
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
    </>
  );
}
