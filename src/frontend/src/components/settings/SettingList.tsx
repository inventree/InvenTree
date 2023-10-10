import { LoadingOverlay, Stack, Text } from '@mantine/core';
import { useContext } from 'react';

import {
  SettingsContext,
  SettingsContextType
} from '../../contexts/SettingsContext';
import { SettingItem } from './SettingItem';

/**
 * Display a list of setting items, based on a list of provided keys
 */
export function SettingList({ keys }: { keys: string[] }) {
  // List of available settings is provided by SettingsContext.Provider
  const settings: SettingsContextType = useContext(SettingsContext);

  return (
    <>
      <Stack spacing="xs">
        <LoadingOverlay visible={settings.settingsQuery?.isLoading ?? false} />
        {keys.map((key) => {
          const setting = settings.settingsData.find((s: any) => s.key === key);
          return (
            <div key={key}>
              {setting ? (
                <SettingItem setting={setting} />
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
