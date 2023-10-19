import { LoadingOverlay, Stack, Text } from '@mantine/core';
import { useEffect } from 'react';

import {
  SettingsStateProps,
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
  keys: string[];
}) {
  useEffect(() => {
    settingsState.fetchSettings();
  }, []);

  return (
    <>
      <Stack spacing="xs">
        {keys.map((key) => {
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
