import { Stack, Text } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { useEffect } from 'react';

import { api } from '../../App';
import { ApiPaths, apiUrl } from '../../states/ApiState';
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

export function MachineSettingList({ pk }: { pk: string }) {
  const { isLoading, isLoadingError, data } = useQuery({
    enabled: true,
    queryKey: ['machine-detail', pk],
    queryFn: () => {
      console.log(
        'FETCH',
        apiUrl(ApiPaths.machine_setting_list).replace('$id', pk)
      );
      return api.get(apiUrl(ApiPaths.machine_setting_list).replace('$id', pk));
    },
    refetchOnMount: false,
    refetchOnWindowFocus: false
  });
  console.log(data);
  if (isLoading) {
    return <h1>Loading</h1>;
  }

  if (isLoadingError) {
    return <h1>Error</h1>;
  }

  return <h1>Loaded</h1>;
}
