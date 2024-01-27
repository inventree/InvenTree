import { t } from '@lingui/macro';
import {
  Button,
  Group,
  Paper,
  Space,
  Stack,
  Switch,
  Text,
  useMantineTheme
} from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { IconEdit } from '@tabler/icons-react';
import { useMemo } from 'react';

import { api } from '../../App';
import { ModelType } from '../../enums/ModelType';
import { openModalApiForm } from '../../functions/forms';
import { apiUrl } from '../../states/ApiState';
import { SettingsStateProps } from '../../states/SettingsState';
import { Setting, SettingType } from '../../states/states';
import { ApiFormFieldType } from '../forms/fields/ApiFormField';

/**
 * Render a single setting value
 */
function SettingValue({
  settingsState,
  setting,
  onChange
}: {
  settingsState: SettingsStateProps;
  setting: Setting;
  onChange?: () => void;
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
        onChange?.();
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
    const fieldDefinition: ApiFormFieldType = {
      value: setting?.value ?? '',
      field_type: setting?.type ?? 'string',
      label: setting?.name,
      description: setting?.description
    };

    // Match related field
    if (
      fieldDefinition.field_type === SettingType.Model &&
      setting.api_url &&
      setting.model_name
    ) {
      fieldDefinition.api_url = setting.api_url;

      // TODO: improve this model matching mechanism
      fieldDefinition.model = setting.model_name.split('.')[1] as ModelType;
    } else if (setting.choices?.length > 0) {
      // Match choices
      fieldDefinition.field_type = SettingType.Choice;
      fieldDefinition.choices = setting?.choices || [];
    }

    openModalApiForm({
      url: settingsState.endpoint,
      pk: setting.key,
      pathParams: settingsState.pathParams,
      method: 'PATCH',
      title: t`Edit Setting`,
      ignorePermissionCheck: true,
      fields: {
        value: fieldDefinition
      },
      onFormSuccess() {
        showNotification({
          title: t`Setting updated`,
          message: t`${setting?.name} updated successfully`,
          color: 'green'
        });
        settingsState.fetchSettings();
        onChange?.();
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
  setting,
  shaded,
  onChange
}: {
  settingsState: SettingsStateProps;
  setting: Setting;
  shaded: boolean;
  onChange?: () => void;
}) {
  const theme = useMantineTheme();

  const style: Record<string, string> = { paddingLeft: '8px' };
  if (shaded) {
    style['backgroundColor'] =
      theme.colorScheme === 'light'
        ? theme.colors.gray[1]
        : theme.colors.gray[9];
  }

  return (
    <Paper style={style}>
      <Group position="apart" p="3">
        <Stack spacing="2" p="4px">
          <Text>
            {setting.name}
            {setting.required ? ' *' : ''}
          </Text>
          <Text size="xs">{setting.description}</Text>
        </Stack>
        <SettingValue
          settingsState={settingsState}
          setting={setting}
          onChange={onChange}
        />
      </Group>
    </Paper>
  );
}
