import { Trans, t } from '@lingui/macro';
import { Stack, Text } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState
} from 'react';
import { useStore } from 'zustand';

import { useApi } from '../../contexts/ApiContext';
import type { ModelType } from '../../enums/ModelType';
import { useEditApiFormModal } from '../../hooks/UseForm';
import { apiUrl } from '../../states/ApiState';
import {
  type SettingsStateProps,
  createMachineSettingsState,
  createPluginSettingsState,
  useGlobalSettingsState,
  useUserSettingsState
} from '../../states/SettingsState';
import type { Setting } from '../../states/states';
import { SettingItem } from './SettingItem';

/**
 * Display a list of setting items, based on a list of provided keys
 */
export function SettingList({
  settingsState,
  keys,
  onChange
}: Readonly<{
  settingsState: SettingsStateProps;
  keys?: string[];
  onChange?: () => void;
}>) {
  useEffect(() => {
    settingsState.fetchSettings();
  }, []);

  const api = useApi();

  const allKeys = useMemo(
    () => settingsState?.settings?.map((s) => s.key) ?? [],
    [settingsState?.settings]
  );

  const [setting, setSetting] = useState<Setting | undefined>(undefined);

  // Determine the field type of the setting
  const fieldType = useMemo(() => {
    if (setting?.choices?.length) {
      return 'choice';
    }

    if (setting?.type != undefined) {
      return setting.type;
    }

    return 'string';
  }, [setting]);

  const editSettingModal = useEditApiFormModal({
    url: settingsState.endpoint,
    pk: setting?.key,
    pathParams: settingsState.pathParams,
    title: t`Edit Setting`,
    fields: {
      value: {
        field_type: fieldType,
        required: setting?.required ?? false,
        label: setting?.name,
        description: setting?.description,
        api_url: setting?.api_url ?? '',
        model: (setting?.model_name?.split('.')[1] as ModelType) ?? null,
        choices: setting?.choices ?? undefined
      }
    },
    successMessage: t`Setting ${setting?.key} updated successfully`,
    onFormSuccess: () => {
      settingsState.fetchSettings();
      onChange?.();
    }
  });

  // Callback for editing a single setting instance
  const onValueEdit = useCallback(
    (setting: Setting) => {
      setSetting(setting);
      editSettingModal.open();
    },
    [editSettingModal]
  );

  // Callback for toggling a single boolean setting instance
  const onValueToggle = useCallback(
    (setting: Setting, value: boolean) => {
      api
        .patch(
          apiUrl(settingsState.endpoint, setting.key, settingsState.pathParams),
          {
            value: value
          }
        )
        .then(() => {
          notifications.hide('setting');
          notifications.show({
            title: t`Setting updated`,
            message: t`Setting ${setting.key} updated successfully`,
            color: 'green',
            id: 'setting'
          });
          onChange?.();
        })
        .catch((error) => {
          notifications.hide('setting');
          notifications.show({
            title: t`Error editing setting`,
            message: error.message,
            color: 'red',
            id: 'setting'
          });
        })
        .finally(() => {
          settingsState.fetchSettings();
        });
    },
    [settingsState]
  );

  return (
    <>
      {editSettingModal.modal}
      <Stack gap='xs'>
        {(keys || allKeys)?.map((key, i) => {
          const setting = settingsState?.settings?.find(
            (s: any) => s.key === key
          );

          if (settingsState?.settings && !setting) {
            console.error(`Setting ${key} not found`);
          }

          return (
            <React.Fragment key={key}>
              {setting ? (
                <SettingItem
                  setting={setting}
                  shaded={i % 2 === 0}
                  onEdit={onValueEdit}
                  onToggle={onValueToggle}
                />
              ) : (
                <Text size='sm' style={{ fontStyle: 'italic' }} c='red'>
                  Setting {key} not found
                </Text>
              )}
            </React.Fragment>
          );
        })}
        {(keys || allKeys)?.length === 0 && (
          <Text style={{ fontStyle: 'italic' }}>
            <Trans>No settings specified</Trans>
          </Text>
        )}
      </Stack>
    </>
  );
}

export function UserSettingList({ keys }: Readonly<{ keys: string[] }>) {
  const userSettings = useUserSettingsState();

  return <SettingList settingsState={userSettings} keys={keys} />;
}

export function GlobalSettingList({ keys }: Readonly<{ keys: string[] }>) {
  const globalSettings = useGlobalSettingsState();

  return <SettingList settingsState={globalSettings} keys={keys} />;
}

export function PluginSettingList({
  pluginKey
}: Readonly<{ pluginKey: string }>) {
  const pluginSettingsStore = useRef(
    createPluginSettingsState({ plugin: pluginKey })
  ).current;
  const pluginSettings = useStore(pluginSettingsStore);

  return <SettingList settingsState={pluginSettings} />;
}

export function MachineSettingList({
  machinePk,
  configType,
  onChange
}: Readonly<{
  machinePk: string;
  configType: 'M' | 'D';
  onChange?: () => void;
}>) {
  const machineSettingsStore = useRef(
    createMachineSettingsState({
      machine: machinePk,
      configType: configType
    })
  ).current;
  const machineSettings = useStore(machineSettingsStore);

  return <SettingList settingsState={machineSettings} onChange={onChange} />;
}
