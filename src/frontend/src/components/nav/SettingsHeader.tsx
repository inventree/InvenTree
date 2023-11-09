import {
  Anchor,
  Button,
  Group,
  Paper,
  Space,
  Stack,
  Text,
  Title
} from '@mantine/core';
import { IconSwitch } from '@tabler/icons-react';
import { ReactNode } from 'react';
import { Link } from 'react-router-dom';

import { StylishText } from '../items/StylishText';

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
  title: string;
  shorthand?: string;
  subtitle?: string;
  switch_condition?: boolean;
  switch_text?: string | ReactNode;
  switch_link?: string;
}) {
  return (
    <Paper shadow="xs" radius="xs" p="xs">
      <Group position="apart">
        <Stack spacing="xs">
          <Group position="left" spacing="xs">
            <StylishText size="xl">{title}</StylishText>
            <Text size="sm">{shorthand}</Text>
          </Group>
          <Text italic>{subtitle}</Text>
        </Stack>
        <Space />
        {switch_text && switch_link && switch_condition && (
          <Anchor component={Link} to={switch_link}>
            <Button variant="outline">
              <Group spacing="sm">
                <IconSwitch size={18} />
                <Text>{switch_text}</Text>
              </Group>
            </Button>
          </Anchor>
        )}
      </Group>
    </Paper>
  );
}
