import { Stack, Text, useMantineTheme } from '@mantine/core';
import { useEffect, useMemo } from 'react';

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
  keys?: string[];
}) {
  useEffect(() => {
    settingsState.fetchSettings();
  }, []);

  const allKeys = useMemo(
    () => settingsState?.settings?.map((s) => s.key),
    [settingsState?.settings]
  );

  const theme = useMantineTheme();

  return (
    <>
      <Stack spacing="xs">
        {(keys || allKeys).map((key, i) => {
          const setting = settingsState?.settings?.find(
            (s: any) => s.key === key
          );

          const style: Record<string, string> = { paddingLeft: '8px' };
          if (i % 2 === 0)
            style['backgroundColor'] =
              theme.colorScheme === 'light'
                ? theme.colors.gray[1]
                : theme.colors.gray[9];

          return (
            <div key={key} style={style}>
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
