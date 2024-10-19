import {
  Button,
  Group,
  Paper,
  Space,
  Stack,
  Switch,
  Text,
  useMantineColorScheme
} from '@mantine/core';
import { IconEdit } from '@tabler/icons-react';
import { useMemo } from 'react';

import type { Setting } from '../../states/states';
import { vars } from '../../theme';
import { Boundary } from '../Boundary';

/**
 * Render a single setting value
 */
function SettingValue({
  setting,
  onEdit,
  onToggle
}: Readonly<{
  setting: Setting;
  onEdit: (setting: Setting) => void;
  onToggle: (setting: Setting, value: boolean) => void;
}>) {
  // Determine the text to display for the setting value
  const valueText: string = useMemo(() => {
    let value = setting.value;

    // If the setting has a choice, display the choice label
    if (setting?.choices && setting?.choices?.length > 0) {
      const choice = setting.choices.find((c) => c.value == setting.value);
      value = choice?.display_name || setting.value;
    }

    if (setting?.units) {
      value = `${value} ${setting.units}`;
    }

    return value;
  }, [setting]);

  switch (setting?.type || 'string') {
    case 'boolean':
      return (
        <Switch
          size='sm'
          radius='lg'
          checked={setting.value.toLowerCase() == 'true'}
          onChange={(event) => onToggle(setting, event.currentTarget.checked)}
          style={{
            paddingRight: '20px'
          }}
        />
      );
    default:
      return valueText ? (
        <Group gap='xs' justify='right'>
          <Space />
          <Button variant='subtle' onClick={() => onEdit(setting)}>
            {valueText}
          </Button>
        </Group>
      ) : (
        <Button variant='subtle' onClick={() => onEdit(setting)}>
          <IconEdit />
        </Button>
      );
  }
}

/**
 * Display a single setting item, and allow editing of the value
 */
export function SettingItem({
  setting,
  shaded,
  onEdit,
  onToggle
}: Readonly<{
  setting: Setting;
  shaded: boolean;
  onEdit: (setting: Setting) => void;
  onToggle: (setting: Setting, value: boolean) => void;
}>) {
  const { colorScheme } = useMantineColorScheme();

  const style: Record<string, string> = { paddingLeft: '8px' };
  if (shaded) {
    style['backgroundColor'] =
      colorScheme === 'light' ? vars.colors.gray[1] : vars.colors.gray[9];
  }

  return (
    <Paper style={style}>
      <Group justify='space-between' p='3'>
        <Stack gap='2' p='4px'>
          <Text>
            {setting.name}
            {setting.required ? ' *' : ''}
          </Text>
          <Text size='xs'>{setting.description}</Text>
        </Stack>
        <Boundary label={`setting-value-${setting.key}`}>
          <SettingValue setting={setting} onEdit={onEdit} onToggle={onToggle} />
        </Boundary>
      </Group>
    </Paper>
  );
}
