import { t } from '@lingui/macro';
import {
  CloseButton,
  Divider,
  Drawer,
  Group,
  Stack,
  Text,
  Tooltip
} from '@mantine/core';

import { TableState } from '../../hooks/UseTable';
import { StylishText } from '../items/StylishText';
import { TableFilter } from './Filter';

/*
 * Render a single table filter item
 */
function FilterItem({ flt }: { flt: TableFilter }) {
  return (
    <Group position="apart" key={flt.name}>
      <Stack spacing="xs">
        <Text size="sm">{flt.label}</Text>
        <Text size="xs">{flt.description}</Text>
      </Stack>
      <Group position="right">
        <Text size="xs">{flt.value}</Text>
        <Tooltip label={t`Remove filter`} withinPortal={true}>
          <CloseButton size="sm" color="red" />
        </Tooltip>
      </Group>
    </Group>
  );
}

export function FilterSelectDrawer({
  availableFilters,
  tableState,
  opened,
  onClose
}: {
  availableFilters: TableFilter[];
  tableState: TableState;
  opened: boolean;
  onClose: () => void;
}) {
  return (
    <Drawer
      size="sm"
      position="right"
      withCloseButton={true}
      opened={opened}
      onClose={onClose}
      title={<StylishText size="lg">{t`Table Filters`}</StylishText>}
    >
      <Stack spacing="sm">
        <Divider />
        {tableState.activeFilters.map((f) => (
          <FilterItem flt={f} />
        ))}
      </Stack>
    </Drawer>
  );
}
