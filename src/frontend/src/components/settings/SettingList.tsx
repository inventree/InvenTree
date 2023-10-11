import { LoadingOverlay, Stack, Text } from '@mantine/core';

import { SettingsStateProps } from '../../states/SettingsState';
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
