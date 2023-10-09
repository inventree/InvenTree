import { Group, Text } from '@mantine/core';

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
      <Group position="apart">
        <Text>{setting.name}</Text>
        <Text>{setting.description}</Text>
        <Text>{setting.type}</Text>
      </Group>
    </>
  );
}
