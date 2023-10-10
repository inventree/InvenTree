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
        <LoadingOverlay visible={settings.settingsQuery?.isFetching ?? false} />
        {keys.map((key) => {
          const setting = settings.settingsData.find((s: any) => s.key === key);
          if (setting) {
            return <SettingItem setting={setting} />;
          } else {
            return (
              <Text size="sm" italic color="red">
                Setting {key} not found
              </Text>
            );
          }
        })}
      </Stack>
    </>
  );
}
