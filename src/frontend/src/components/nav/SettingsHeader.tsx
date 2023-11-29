import { Anchor, Group, Stack, Text, Title } from '@mantine/core';
import { IconSwitch } from '@tabler/icons-react';
import { ReactNode } from 'react';
import { Link } from 'react-router-dom';

/**
 * Construct a settings page header with interlinks to one other settings page
 */
export function SettingsHeader({
  title,
  shorthand,
  subtitle,
  switch_condition = true,
  switch_text,
  switch_link
}: {
  title: string | ReactNode;
  shorthand?: string;
  subtitle?: string | ReactNode;
  switch_condition?: boolean;
  switch_text?: string | ReactNode;
  switch_link?: string;
}) {
  return (
    <Stack spacing="0" ml={'sm'}>
      <Group>
        <Title order={3}>{title}</Title>
        {shorthand && <Text c="dimmed">({shorthand})</Text>}
      </Group>
      <Group>
        <Text c="dimmed">{subtitle}</Text>
        {switch_text && switch_link && switch_condition && (
          <Anchor component={Link} to={switch_link}>
            <IconSwitch size={14} />
            {switch_text}
          </Anchor>
        )}
      </Group>
    </Stack>
  );
}
