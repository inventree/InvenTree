import { t } from '@lingui/core/macro';
import {
  Button,
  Group,
  Paper,
  Space,
  Stack,
  Switch,
  Text,
  Tooltip,
  useMantineColorScheme
} from '@mantine/core';
import { IconEdit } from '@tabler/icons-react';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { ModelInformationDict } from '@lib/enums/ModelInformation';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import type { Setting } from '@lib/types/Settings';
import { api } from '../../App';
import { vars } from '../../theme';
import { Boundary } from '../Boundary';
import { RenderInstance } from '../render/Instance';

type ConfirmResult = {
  requires_confirmation: boolean;
  confirmed: boolean;
  proceed?: boolean;
};
function confirmSettingChange(setting: Setting): ConfirmResult {
  if (setting.confirm) {
    const confirmed = window.confirm(
      setting.confirm_text || t`Do you want to proceed to change this setting?`
    );
    return {
      requires_confirmation: true,
      confirmed: confirmed || false,
      proceed: confirmed
    };
  }
  return { requires_confirmation: false, confirmed: false, proceed: true };
}
/**
 * Render a single setting value
 */
function SettingValue({
  setting,
  onEdit,
  onToggle
}: Readonly<{
  setting: Setting;
  onEdit: (setting: Setting, confirmed: boolean) => void;
  onToggle: (setting: Setting, value: boolean, confirmed: boolean) => void;
}>) {
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

  const [modelInstance, setModelInstance] = useState<any>(null);

  // Launch the edit dialog for this setting
  const editSetting = useCallback(() => {
    if (!setting.read_only) {
      const confirm = confirmSettingChange(setting);
      if (!confirm.proceed) return;
      onEdit(setting, confirm.confirmed);
    }
  }, [setting, onEdit]);

  // Toggle the setting value (if it is a boolean)
  const toggleSetting = useCallback(
    (event: any) => {
      if (!setting.read_only) {
        const confirm = confirmSettingChange(setting);
        if (!confirm.proceed) return;
        onToggle(setting, event.currentTarget.checked, confirm.confirmed);
      }
    },
    [setting, onToggle]
  );

  // Does this setting map to an internal database model?
  const modelType: ModelType | null = useMemo(() => {
    if (setting.model_name) {
      const model = setting.model_name.split('.')[1];
      return ModelType[model as keyof typeof ModelType] || null;
    }
    return null;
  }, [setting]);

  useEffect(() => {
    setModelInstance(null);

    if (modelType && setting.value) {
      const endpoint = ModelInformationDict[modelType].api_endpoint;

      api
        .get(apiUrl(endpoint, setting.value))
        .then((response) => {
          if (response.data) {
            setModelInstance(response.data);
          } else {
            setModelInstance(null);
          }
        })
        .catch((error) => {
          setModelInstance(null);
        });
    }
  }, [setting, modelType]);

  // If a full model instance is available, render it
  if (modelInstance && modelType && setting.value) {
    return (
      <Group justify='right' gap='xs'>
        <RenderInstance instance={modelInstance} model={modelType} />
        <Button
          aria-label={`edit-setting-${setting.key}`}
          variant='subtle'
          disabled={setting.read_only}
          onClick={editSetting}
        >
          <IconEdit />
        </Button>
      </Group>
    );
  }

  switch (setting?.type || 'string') {
    case 'boolean':
      return (
        <Switch
          size='sm'
          radius='lg'
          aria-label={`toggle-setting-${setting.key}`}
          disabled={setting.read_only}
          checked={setting.value.toString().toLowerCase() == 'true'}
          onChange={toggleSetting}
          wrapperProps={{
            'aria-label': `setting-${setting.key}-wrapper`
          }}
          style={{
            paddingRight: '20px'
          }}
        />
      );
    default:
      return valueText ? (
        <Group gap='xs' justify='right'>
          <Space />
          <Button
            aria-label={`edit-setting-${setting.key}`}
            variant='subtle'
            disabled={setting.read_only}
            onClick={editSetting}
          >
            {valueText}
          </Button>
        </Group>
      ) : (
        <Button
          aria-label={`edit-setting-${setting.key}`}
          variant='subtle'
          disabled={setting.read_only}
          onClick={editSetting}
        >
          <IconEdit />
        </Button>
      );
  }
}

/**
 * Display a single setting item, and allow editing of the value
 */
export function SettingItem({
  setting,
  shaded,
  onEdit,
  onToggle
}: Readonly<{
  setting: Setting;
  shaded: boolean;
  onEdit: (setting: Setting, confirmed: boolean) => void;
  onToggle: (setting: Setting, value: boolean, confirmed: boolean) => void;
}>) {
  const { colorScheme } = useMantineColorScheme();

  const style: Record<string, string> = { paddingLeft: '8px' };
  if (shaded) {
    style['backgroundColor'] =
      colorScheme === 'light' ? vars.colors.gray[1] : vars.colors.gray[9];
  }

  return (
    <Paper style={style}>
      <Group justify='space-between' p='3'>
        <Stack gap='2' p='4px'>
          <Text>
            {setting.name}
            {setting.required ? ' *' : ''}
          </Text>
          <Text size='xs'>{setting.description}</Text>
        </Stack>
        <Boundary label={`setting-value-${setting.key}`}>
          <Group gap='xs' justify='right'>
            {setting.confirm && (
              <Tooltip label={t`This setting requires confirmation`}>
                <IconEdit color={vars.colors.yellow[7]} size={16} />
              </Tooltip>
            )}
            <SettingValue
              setting={setting}
              onEdit={onEdit}
              onToggle={onToggle}
            />
          </Group>
        </Boundary>
      </Group>
    </Paper>
  );
}
