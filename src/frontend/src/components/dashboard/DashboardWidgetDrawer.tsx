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
  TextInput,
  Tooltip
} from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import { IconBackspace, IconLayoutGridAdd } from '@tabler/icons-react';
import { useMemo, useState } from 'react';

import { useDashboardItems } from '../../hooks/UseDashboardItems';
import { StylishText } from '../items/StylishText';

/**
 * Drawer allowing the user to add new widgets to the dashboard.
 */
export default function DashboardWidgetDrawer({
  opened,
  onClose,
  onAddWidget,
  currentWidgets
}: Readonly<{
  opened: boolean;
  onClose: () => void;
  onAddWidget: (widget: string) => void;
  currentWidgets: string[];
}>) {
  // Load available widgets
  const availableWidgets = useDashboardItems();

  const [filter, setFilter] = useState<string>('');
  const [filterText] = useDebouncedValue(filter, 500);

  // Memoize available (not currently used) widgets
  const unusedWidgets = useMemo(() => {
    return (
      availableWidgets.items.filter(
        (widget) => !currentWidgets.includes(widget.label)
      ) ?? []
    );
  }, [availableWidgets.items, currentWidgets]);

  // Filter widgets based on search text
  const filteredWidgets = useMemo(() => {
    const words = filterText.trim().toLowerCase().split(' ');

    return unusedWidgets.filter((widget) => {
      return words.every((word) =>
        widget.title.toLowerCase().includes(word.trim())
      );
    });
  }, [unusedWidgets, filterText]);

  return (
    <Drawer
      position='right'
      size='50%'
      opened={opened}
      onClose={onClose}
      title={
        <Group justify='space-between' wrap='nowrap'>
          <StylishText size='lg'>Add Dashboard Widgets</StylishText>
        </Group>
      }
    >
      <Stack gap='xs'>
        <Divider />
        <TextInput
          aria-label='dashboard-widgets-filter-input'
          placeholder={t`Filter dashboard widgets`}
          value={filter}
          onChange={(event) => setFilter(event.currentTarget.value)}
          rightSection={
            filter && (
              <IconBackspace
                aria-label='dashboard-widgets-filter-clear'
                color='red'
                onClick={() => setFilter('')}
              />
            )
          }
          styles={{ root: { width: '100%' } }}
        />
        <Table>
          <Table.Tbody>
            {filteredWidgets.map((widget) => (
              <Table.Tr key={widget.label}>
                <Table.Td>
                  <Tooltip
                    position='left'
                    label={t`Add this widget to the dashboard`}
                  >
                    <ActionIcon
                      aria-label={`add-widget-${widget.label}`}
                      variant='transparent'
                      color='green'
                      onClick={() => {
                        onAddWidget(widget.label);
                      }}
                    >
                      <IconLayoutGridAdd />
                    </ActionIcon>
                  </Tooltip>
                </Table.Td>
                <Table.Td>
                  <Text>{widget.title}</Text>
                </Table.Td>
                <Table.Td>
                  <Text size='sm'>{widget.description}</Text>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
        {unusedWidgets.length === 0 && (
          <Alert color='blue' title={t`No Widgets Available`}>
            <Text>{t`There are no more widgets available for the dashboard`}</Text>
          </Alert>
        )}
      </Stack>
    </Drawer>
  );
}
