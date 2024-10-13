import { Trans, t } from '@lingui/macro';
import {
  ActionIcon,
  Group,
  Indicator,
  Menu,
  Paper,
  Tooltip
} from '@mantine/core';
import {
  IconCircleCheck,
  IconDotsVertical,
  IconLayout2,
  IconLayoutGridAdd,
  IconLayoutGridRemove
} from '@tabler/icons-react';
import { link } from 'fs';
import { useMemo } from 'react';

import { ModelType } from '../../enums/ModelType';
import { UserPermissions, UserRoles } from '../../enums/Roles';
import useInstanceName from '../../hooks/UseInstanceName';
import { useGlobalSettingsState } from '../../states/SettingsState';
import { useUserState } from '../../states/UserState';
import { MenuLinkItem } from '../items/MenuLinks';
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
  const user = useUserState();
  const instanceName = useInstanceName();

  const title = useMemo(() => {
    const username = user.username();

    return (
      <StylishText size="lg">{`${instanceName} - ${username}`}</StylishText>
    );
  }, [user, instanceName]);

  return (
    <Paper p="sm" shadow="xs">
      <Group justify="space-between" wrap="nowrap">
        {title}

        <Group justify="right" wrap="nowrap">
          {(editing || removing) && (
            <Tooltip
              label={t`Accept Layout`}
              onClick={() => {
                if (editing) {
                  onToggleEdit();
                } else if (removing) {
                  onToggleRemove();
                }
              }}
            >
              <ActionIcon color="green" variant="transparent">
                <IconCircleCheck />
              </ActionIcon>
            </Tooltip>
          )}
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
