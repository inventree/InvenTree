import { ApiEndpoints } from '@lib/index';
import type { SettingsStateProps } from '@lib/types/Settings';
import { t } from '@lingui/core/macro';
import { Accordion, Alert, Group, Stack, Text } from '@mantine/core';
import { IconInfoCircle } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';
import {
  PluginSettingList,
  PluginUserSettingList
} from '../../../components/settings/SettingList';
import { useInstance } from '../../../hooks/UseInstance';

function PluginSettingGroupItem({
  global,
  pluginKey,
  pluginName,
  pluginDescription
}: {
  global: boolean;
  pluginKey: string;
  pluginName: string;
  pluginDescription?: string;
}) {
  // Hide the accordion item if there are no settings for this plugin
  const [count, setCount] = useState<number>(0);

  // Callback once the plugin settings have been loaded
  const onLoaded = useCallback(
    (settings: SettingsStateProps) => {
      setCount(settings.settings?.length || 0);
    },
    [pluginKey]
  );

  return (
    <Accordion.Item
      key={`plugin-${pluginKey}`}
      value={pluginKey}
      hidden={count === 0}
    >
      <Accordion.Control>
        <Group>
          <Text size='lg'>{pluginName}</Text>
          {pluginDescription && <Text size='sm'>{pluginDescription}</Text>}
        </Group>
      </Accordion.Control>
      <Accordion.Panel>
        {global ? (
          <PluginSettingList pluginKey={pluginKey} onLoaded={onLoaded} />
        ) : (
          <PluginUserSettingList pluginKey={pluginKey} onLoaded={onLoaded} />
        )}
      </Accordion.Panel>
    </Accordion.Item>
  );
}

/**
 * Displays an accordion of user-specific plugin settings
 * - Each element in the accordion corresponds to a plugin
 * - Each plugin can have multiple settings
 * - If a plugin has no settings, it will not be displayed
 */
export default function PluginSettingsGroup({
  mixin,
  global
}: {
  global: boolean;
  mixin?: string;
}) {
  const mixins: string = useMemo(() => {
    const mixinList: string[] = ['settings'];

    if (mixin) {
      mixinList.push(mixin);
    }

    return mixinList.join(',');
  }, [mixin]);

  // All *active* plugins which require settings
  const activePlugins = useInstance({
    endpoint: ApiEndpoints.plugin_list,
    params: {
      active: true,
      mixin: mixins
    },
    hasPrimaryKey: false,
    defaultValue: []
  });

  return (
    <Stack gap='xs'>
      <Alert color='blue' icon={<IconInfoCircle />}>
        <Text>{t`The settings below are specific to each available plugin`}</Text>
      </Alert>
      <Accordion multiple>
        {activePlugins.instance?.map((plugin: any) => {
          return (
            <PluginSettingGroupItem
              global={global}
              key={plugin.key}
              pluginKey={plugin.key}
              pluginName={plugin.meta?.human_name ?? plugin.name}
              pluginDescription={plugin?.meta?.description}
            />
          );
        })}
      </Accordion>
    </Stack>
  );
}
