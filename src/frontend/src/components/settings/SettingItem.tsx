import { t } from '@lingui/macro';
import { Button, Group, Space, Stack, Switch, Text } from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { useContext } from 'react';

import { api } from '../../App';
import { SettingsContext } from '../../contexts/SettingsContext';
import { openModalApiForm } from '../../functions/forms';

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
function SettingValue({ setting }: { setting: SettingType }) {
  const settings = useContext(SettingsContext);

  // TODO: extract URL from top-level query (only global settings work currently)
  const url = '/settings/global/';

  // Callback function when a boolean value is changed
  function onToggle(value: boolean) {
    api
      .patch(`${url}${setting.key}/`, { value: value })
      .then(() => {
        settings.settingsQuery?.refetch();
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

  // Callback function to open the edit dialog (for non-boolean settings)
  function onEditButton() {
    openModalApiForm({
      name: 'setting-edit',
      url: url,
      pk: setting.key,
      method: 'PATCH',
      title: t`Edit Setting`,
      ignoreOptionsCheck: true,
      fields: {
        value: {
          value: setting?.value ?? '',
          fieldType: setting?.type ?? 'string',
          choices: setting?.choices || null,
          label: setting?.name,
          description: setting?.description
        }
      },
      onFormSuccess() {
        settings.settingsQuery?.refetch();
      }
    });
  }

  switch (setting?.type || 'string') {
    case 'boolean':
      return (
        <Switch
          size="sm"
          checked={setting.value.toLowerCase() == 'true'}
          onChange={(event) => onToggle(event.currentTarget.checked)}
        />
      );
    default:
      return (
        <Group spacing="xs" position="right">
          <Space />
          <Button variant="subtle" onClick={onEditButton}>
            {setting.value || 'no value'}
          </Button>
        </Group>
      );
  }
}

/**
 * Display a single setting item, and allow editing of the value
 */
export function SettingItem({ setting }: { setting: SettingType }) {
  return (
    <>
      <Group position="apart" p="10">
        <Stack spacing="2">
          <Text>{setting.name}</Text>
          <Text size="xs">{setting.description}</Text>
        </Stack>
        <SettingValue setting={setting} />
      </Group>
    </>
  );
}
