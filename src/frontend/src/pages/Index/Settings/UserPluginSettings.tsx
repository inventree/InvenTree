import { ApiEndpoints } from '@lib/index';
import type { SettingsStateProps } from '@lib/types/Settings';
import { t } from '@lingui/core/macro';
import { Accordion, Alert, Group, Stack, Text } from '@mantine/core';
import { IconInfoCircle } from '@tabler/icons-react';
import { useCallback, useState } from 'react';
import { PluginUserSettingList } from '../../../components/settings/SettingList';
import { useInstance } from '../../../hooks/UseInstance';

function PluginUserSetting({
  pluginKey,
  pluginName,
  pluginDescription
}: {
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
        <PluginUserSettingList pluginKey={pluginKey} onLoaded={onLoaded} />
      </Accordion.Panel>
    </Accordion.Item>
  );
}

export default function UserPluginSettings() {
  // All *active* plugins which require settings
  const activePlugins = useInstance({
    endpoint: ApiEndpoints.plugin_list,
    params: {
      active: true,
      mixin: 'settings'
    },
    hasPrimaryKey: false,
    defaultValue: []
  });

  return (
    <Stack gap='xs'>
      <Alert color='blue' icon={<IconInfoCircle />}>
        <Text>{t`Configuration for plugins which require user specific settings`}</Text>
      </Alert>
      <Accordion multiple>
        {activePlugins.instance?.map((plugin: any) => {
          return (
            <PluginUserSetting
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
