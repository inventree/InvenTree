import { Group, Paper, Stack, Text } from '@mantine/core';

export type SettingType = {
  pk: number;
  key: string;
  value: string;
  name: string;
  description: string;
  type: string;
  choices: any[];
  model_name: string;
  api_url: string;
};

/**
 * Display a single setting item
 */
export function SettingItem({ setting }: { setting: SettingType }) {
  return (
    <>
      <Group position="apart" p="10">
        <Stack spacing="2">
          <Text>{setting.name}</Text>
          <Text size="xs">{setting.description}</Text>
        </Stack>
        <Text>{setting.type}</Text>
      </Group>
    </>
  );
}
