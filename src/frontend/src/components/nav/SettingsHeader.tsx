import { t } from '@lingui/macro';
import {
  Anchor,
  Group,
  SegmentedControl,
  Stack,
  Text,
  Title
} from '@mantine/core';
import { IconSwitch } from '@tabler/icons-react';
import { ReactNode } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { useUserState } from '../../states/UserState';
import { StylishText } from '../items/StylishText';

interface SettingsHeaderInterface {
  label: string;
  title: string;
  shorthand?: string;
  subtitle?: string | ReactNode;
}

/**
 * Construct a settings page header with interlinks to one other settings page
 */
export function SettingsHeader({
  label,
  title,
  shorthand,
  subtitle
}: Readonly<SettingsHeaderInterface>) {
  const user = useUserState();
  const navigate = useNavigate();

  return (
    <Group justify="space-between">
      <Stack gap="0" ml={'sm'}>
        <Group>
          <StylishText size="xl">{title}</StylishText>
          {shorthand && <Text c="dimmed">({shorthand})</Text>}
        </Group>
        <Group>{subtitle ? <Text c="dimmed">{subtitle}</Text> : null}</Group>
      </Stack>
      {user.isStaff() && (
        <SegmentedControl
          data={[
            { value: 'user', label: t`User Settings` },
            { value: 'system', label: t`System Settings` },
            { value: 'admin', label: t`Admin Center` }
          ]}
          onChange={(value) => navigate(`/settings/${value}`)}
          value={label}
        />
      )}
    </Group>
  );
}
