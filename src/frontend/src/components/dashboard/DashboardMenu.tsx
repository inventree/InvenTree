import { Trans } from '@lingui/macro';
import { ActionIcon, Group, Indicator, Menu, Paper } from '@mantine/core';
import {
  IconArrowBackUpDouble,
  IconCircleCheck,
  IconCirclePlus,
  IconDotsVertical,
  IconLayout2,
  IconLayoutGridAdd,
  IconLayoutGridRemove
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
  removing,
  onAddWidget,
  onToggleEdit,
  onToggleRemove
}: {
  editing: boolean;
  removing: boolean;
  onAddWidget: () => void;
  onToggleEdit: () => void;
  onToggleRemove: () => void;
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

              {!editing && !removing && (
                <Menu.Item
                  leftSection={<IconLayout2 color="blue" size={14} />}
                  onClick={onToggleEdit}
                >
                  <Trans>Edit Layout</Trans>
                </Menu.Item>
              )}

              {!editing && !removing && (
                <Menu.Item
                  leftSection={<IconLayoutGridAdd color="green" size={14} />}
                  onClick={onAddWidget}
                >
                  <Trans>Add Widget</Trans>
                </Menu.Item>
              )}

              {!editing && !removing && (
                <Menu.Item
                  leftSection={<IconLayoutGridRemove color="red" size={14} />}
                  onClick={onToggleRemove}
                >
                  <Trans>Remove Widgets</Trans>
                </Menu.Item>
              )}

              {(editing || removing) && (
                <Menu.Item
                  leftSection={<IconCircleCheck color="green" size={14} />}
                  onClick={() => {
                    if (editing) {
                      onToggleEdit();
                    } else if (removing) {
                      onToggleRemove();
                    }
                  }}
                >
                  <Trans>Accept Layout</Trans>
                </Menu.Item>
              )}
            </Menu.Dropdown>
          </Menu>
        </Group>
      </Group>
    </Paper>
  );
}
