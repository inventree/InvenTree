import { t } from '@lingui/macro';
import { Button, Group, Space, Stack, Switch, Text } from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { IconEdit } from '@tabler/icons-react';
import { useContext, useMemo } from 'react';

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
  units: string;
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
    let field_type = setting?.type ?? 'string';

    if (setting?.choices && setting?.choices?.length > 0) {
      field_type = 'choice';
    }

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
          field_type: field_type,
          choices: setting?.choices || [],
          label: setting?.name,
          description: setting?.description
        }
      },
      onFormSuccess() {
        settings.settingsQuery?.refetch();
      }
    });
  }

  // Determine the text to display for the setting value
  const valueText: string = useMemo(() => {
    let value = setting.value;

    // If the setting has a choice, display the choice label
    if (setting?.choices && setting?.choices?.length > 0) {
      const choice = setting.choices.find((c) => c.value == setting.value);
      value = choice?.display_name || setting.value;
    }

    if (setting?.units) {
      value = `${value} ${setting.units}`;
    }

    return value;
  }, [setting]);

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
      return valueText ? (
        <Group spacing="xs" position="right">
          <Space />
          <Button variant="subtle" onClick={onEditButton}>
            {valueText}
          </Button>
        </Group>
      ) : (
        <Button variant="subtle" onClick={onEditButton}>
          <IconEdit />
        </Button>
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
