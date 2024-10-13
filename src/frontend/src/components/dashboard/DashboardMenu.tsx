import { Trans } from '@lingui/macro';
import { ActionIcon, Group, Indicator, Menu, Paper } from '@mantine/core';
import {
  IconArrowBackUpDouble,
  IconCirclePlus,
  IconDotsVertical,
  IconLayout2
} from '@tabler/icons-react';
import { useMemo } from 'react';

import { useGlobalSettingsState } from '../../states/SettingsState';
import { useUserState } from '../../states/UserState';
import { StylishText } from '../items/StylishText';

/**
 * A menu for editing the dashboard layout
 */
export default function DashboardMenu({
  editing,
  onAddWidget,
  onToggleEdit
}: {
  editing: boolean;
  onAddWidget: () => void;
  onToggleEdit: () => void;
}) {
  const globalSettings = useGlobalSettingsState();
  const user = useUserState();

  const title = useMemo(() => {
    const instance = globalSettings.getSetting(
      'INVENTREE_INSTANCE',
      'InvenTree'
    );
    const username = user.username();

    return <StylishText size="lg">{`${instance} - ${username}`}</StylishText>;
  }, [user, globalSettings]);

  return (
    <Paper p="sm" shadow="xs">
      <Group justify="space-between" wrap="nowrap">
        {title}

        <Group justify="right" wrap="nowrap">
          <Menu
            shadow="md"
            width={200}
            openDelay={100}
            closeDelay={400}
            position="bottom-end"
          >
            <Menu.Target>
              <Indicator
                color="red"
                position="bottom-start"
                processing
                disabled={!editing}
              >
                <ActionIcon variant="transparent">
                  <IconDotsVertical />
                </ActionIcon>
              </Indicator>
            </Menu.Target>

            <Menu.Dropdown>
              <Menu.Label>
                <Trans>Dashboard</Trans>
              </Menu.Label>

              <Menu.Item
                leftSection={<IconCirclePlus size={14} />}
                onClick={onAddWidget}
              >
                <Trans>Add Widget</Trans>
              </Menu.Item>

              {editing && (
                <Menu.Item
                  hidden={!editing}
                  leftSection={<IconArrowBackUpDouble size={14} />}
                  onClick={() => {
                    // TODO: Reset layout function
                  }}
                >
                  <Trans>Reset Layout</Trans>
                </Menu.Item>
              )}
              <Menu.Item
                hidden={!editing}
                leftSection={
                  <IconLayout2 size={14} color={editing ? 'red' : undefined} />
                }
                onClick={onToggleEdit}
              >
                {editing ? (
                  <Trans>Accept Layout</Trans>
                ) : (
                  <Trans>Edit Layout</Trans>
                )}
              </Menu.Item>
            </Menu.Dropdown>
          </Menu>
        </Group>
      </Group>
    </Paper>
  );
}
