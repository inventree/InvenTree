import { Stack, Text } from '@mantine/core';

import { SettingItem, SettingType } from './SettingItem';

/**
 * Display a list of setting items, based on a list of provided keys
 */
export function SettingList({
  settings,
  keys
}: {
  settings: SettingType[];
  keys: string[];
}) {
  return (
    <>
      <Stack spacing="xs">
        {keys.map((key) => {
          const setting = settings.find((setting) => setting.key === key);
          if (setting) {
            return <SettingItem setting={setting} />;
          }
        })}
      </Stack>
    </>
  );
}
