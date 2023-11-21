import { t } from '@lingui/macro';
import { Button, Group, Space, Stack, Switch, Text } from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { IconEdit } from '@tabler/icons-react';
import { useMemo } from 'react';

import { api } from '../../App';
import { openModalApiForm } from '../../functions/forms';
import { apiUrl } from '../../states/ApiState';
import { SettingsStateProps } from '../../states/SettingsState';
import { Setting, SettingType } from '../../states/states';

/**
 * Render a single setting value
 */
function SettingValue({
  settingsState,
  setting
}: {
  settingsState: SettingsStateProps;
  setting: Setting;
}) {
  // Callback function when a boolean value is changed
  function onToggle(value: boolean) {
    api
      .patch(
        apiUrl(settingsState.endpoint, setting.key, settingsState.pathParams),
        { value: value }
      )
      .then(() => {
        showNotification({
          title: t`Setting updated`,
          message: t`${setting?.name} updated successfully`,
          color: 'green'
        });
        settingsState.fetchSettings();
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
      field_type = SettingType.Choice;
    }

    openModalApiForm({
      url: settingsState.endpoint,
      pk: setting.key,
      pathParams: settingsState.pathParams,
      method: 'PATCH',
      title: t`Edit Setting`,
      ignorePermissionCheck: true,
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
        showNotification({
          title: t`Setting updated`,
          message: t`${setting?.name} updated successfully`,
          color: 'green'
        });
        settingsState.fetchSettings();
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
          radius="lg"
          checked={setting.value.toLowerCase() == 'true'}
          onChange={(event) => onToggle(event.currentTarget.checked)}
          style={{
            paddingRight: '20px'
          }}
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
export function SettingItem({
  settingsState,
  setting
}: {
  settingsState: SettingsStateProps;
  setting: Setting;
}) {
  return (
    <>
      <Group position="apart" p="10">
        <Stack spacing="2">
          <Text>{setting.name}</Text>
          <Text size="xs">{setting.description}</Text>
        </Stack>
        <SettingValue settingsState={settingsState} setting={setting} />
      </Group>
    </>
  );
}
