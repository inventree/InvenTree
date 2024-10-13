import { t } from '@lingui/macro';
import {
  ActionIcon,
  Alert,
  Divider,
  Drawer,
  Group,
  Stack,
  Table,
  Text,
  Tooltip
} from '@mantine/core';
import { IconLayoutGridAdd } from '@tabler/icons-react';
import { useMemo } from 'react';

import { StylishText } from '../items/StylishText';
import AvailableDashboardWidgets from './DashboardWidgetLibrary';

/**
 * Drawer allowing the user to add new widgets to the dashboard.
 */
export default function DashboardWidgetDrawer({
  opened,
  onClose,
  onAddWidget,
  currentWidgets
}: {
  opened: boolean;
  onClose: () => void;
  onAddWidget: (widget: string) => void;
  currentWidgets: string[];
}) {
  // Memoize all available widgets
  const allWidgets = useMemo(() => AvailableDashboardWidgets(), []);

  // Memoize available (not currently used) widgets
  const availableWidgets = useMemo(() => {
    return (
      allWidgets.filter((widget) => !currentWidgets.includes(widget.label)) ??
      []
    );
  }, [allWidgets, currentWidgets]);

  return (
    <Drawer
      position="right"
      size="50%"
      opened={opened}
      onClose={onClose}
      title={
        <Group justify="space-between" wrap="nowrap">
          <StylishText size="lg">Add Dashboard Widgets</StylishText>
        </Group>
      }
    >
      <Stack gap="xs">
        <Divider />
        <Table>
          <Table.Tbody>
            {availableWidgets.map((widget) => (
              <Table.Tr>
                <Table.Td>
                  <Tooltip
                    position="left"
                    label={t`Add this widget to the dashboard`}
                  >
                    <ActionIcon
                      aria-label={`add-widget-${widget.label}`}
                      variant="transparent"
                      color="green"
                      onClick={() => {
                        onAddWidget(widget.label);
                      }}
                    >
                      <IconLayoutGridAdd></IconLayoutGridAdd>
                    </ActionIcon>
                  </Tooltip>
                </Table.Td>
                <Table.Td>
                  <Text>{widget.title}</Text>
                </Table.Td>
                <Table.Td>
                  <Text size="sm">{widget.description}</Text>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
        {availableWidgets.length === 0 && (
          <Alert color="blue" title={t`No Widgets Available`}>
            <Text>{t`There are no more widgets available for the dashboard`}</Text>
          </Alert>
        )}
      </Stack>
    </Drawer>
  );
}
