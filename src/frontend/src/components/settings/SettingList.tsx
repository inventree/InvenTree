import { Stack, Text } from '@mantine/core';
import { useEffect, useMemo, useRef } from 'react';
import { useStore } from 'zustand';

import {
  SettingsStateProps,
  createMachineSettingsState,
  useGlobalSettingsState,
  useUserSettingsState
} from '../../states/SettingsState';
import { SettingItem } from './SettingItem';

/**
 * Display a list of setting items, based on a list of provided keys
 */
export function SettingList({
  settingsState,
  keys
}: {
  settingsState: SettingsStateProps;
  keys?: string[];
}) {
  useEffect(() => {
    settingsState.fetchSettings();
  }, []);

  const allKeys = useMemo(
    () => settingsState?.settings?.map((s) => s.key),
    [settingsState?.settings]
  );

  return (
    <>
      <Stack spacing="xs">
        {(keys || allKeys).map((key) => {
          const setting = settingsState?.settings?.find(
            (s: any) => s.key === key
          );
          return (
            <div key={key}>
              {setting ? (
                <SettingItem settingsState={settingsState} setting={setting} />
              ) : (
                <Text size="sm" italic color="red">
                  Setting {key} not found
                </Text>
              )}
            </div>
          );
        })}
      </Stack>
    </>
  );
}

export function UserSettingList({ keys }: { keys: string[] }) {
  const userSettings = useUserSettingsState();

  return <SettingList settingsState={userSettings} keys={keys} />;
}

export function GlobalSettingList({ keys }: { keys: string[] }) {
  const globalSettings = useGlobalSettingsState();

  return <SettingList settingsState={globalSettings} keys={keys} />;
}

export function MachineSettingList({
  machinePk,
  configType
}: {
  machinePk: string;
  configType: 'M' | 'D';
}) {
  const machineSettingsStore = useRef(
    createMachineSettingsState({
      machine: machinePk,
      configType: configType
    })
  ).current;
  const machineSettings = useStore(machineSettingsStore);

  return <SettingList settingsState={machineSettings} />;
}
