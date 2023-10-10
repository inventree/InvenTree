import { t } from '@lingui/macro';
import { Group, Stack, Switch, Text } from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { useContext } from 'react';

import { api } from '../../App';
import { SettingsContext } from '../../contexts/SettingsContext';

export type SettingType = {
  pk: number;
  key: string;
  value: string;
  name: string;
  description: string;
  type: string;
  choices: any[];
  model_name: string;
  api_url: string;
};

/**
 * Render a single setting value
 */
function SettingValue({
  setting,
  onEdit
}: {
  setting: SettingType;
  onEdit: (value: any) => void;
}) {
  switch (setting?.type || 'string') {
    case 'boolean':
      return (
        <Switch
          size="sm"
          checked={setting.value.toLowerCase() == 'true'}
          onChange={(event) => onEdit(event.currentTarget.checked)}
        />
      );
    default:
      return (
        <Text>
          {setting.value} - {setting.type}
        </Text>
      );
  }
}

/**
 * Display a single setting item, and allow editing of the value
 */
export function SettingItem({ setting }: { setting: SettingType }) {
  const settings = useContext(SettingsContext);

  // Callback function when the particular setting value is changed
  function onEdit(value: any) {
    // TODO: Get URL from top level query
    let url = `/settings/global/${setting.key}/`;

    api
      .patch(url, { value: value })
      .then(() => {
        settings?.settingsQuery?.refetch();
      })
      .catch((error) => {
        console.log('Error editing setting', error);
        showNotification({
          title: t`Error editing setting`,
          message: error.message,
          color: 'red'
        });
      });
  }

  return (
    <>
      <Group position="apart" p="10">
        <Stack spacing="2">
          <Text>{setting.name}</Text>
          <Text size="xs">{setting.description}</Text>
        </Stack>
        <SettingValue setting={setting} onEdit={onEdit} />
      </Group>
    </>
  );
}
