import { t } from '@lingui/macro';
import {
  ActionIcon,
  Button,
  CloseButton,
  Divider,
  Drawer,
  Group,
  Paper,
  Select,
  Stack,
  Text,
  Tooltip
} from '@mantine/core';
import { IconCircleX } from '@tabler/icons-react';
import { forwardRef, useCallback, useEffect, useMemo, useState } from 'react';

import { TableState } from '../../hooks/UseTable';
import { StylishText } from '../items/StylishText';
import { TableFilter } from './Filter';

/*
 * Render a single table filter item
 */
function FilterItem({
  flt,
  tableState
}: {
  flt: TableFilter;
  tableState: TableState;
}) {
  const removeFilter = useCallback(() => {
    let newFilters = tableState.activeFilters.filter(
      (f) => f.name !== flt.name
    );
    tableState.setActiveFilters(newFilters);
  }, [flt]);

  return (
    <Paper p="sm" shadow="sm" radius="xs">
      <Group position="apart" key={flt.name}>
        <Stack spacing="xs">
          <Text size="sm">{flt.label}</Text>
          <Text size="xs">{flt.description}</Text>
        </Stack>
        <Group position="right">
          <Text size="xs">{flt.value}</Text>
          <Tooltip label={t`Remove filter`} withinPortal={true}>
            <CloseButton size="md" color="red" onClick={removeFilter} />
          </Tooltip>
        </Group>
      </Group>
    </Paper>
  );
}

interface FilterProps extends React.ComponentPropsWithoutRef<'div'> {
  name: string;
  label: string;
  description?: string;
}

/*
 * Custom component for the filter select
 */
const FilterSelectItem = forwardRef<HTMLDivElement, FilterProps>(
  ({ name, label, description, ...others }, ref) => (
    <div ref={ref} {...others}>
      <Text size="sm">{label}</Text>
      <Text size="xs">{description}</Text>
    </div>
  )
);

function FilterAddGroup({
  tableState,
  availableFilters
}: {
  tableState: TableState;
  availableFilters: TableFilter[];
}) {
  const filterOptions = useMemo(() => {
    let activeFilterNames = tableState.activeFilters.map((flt) => flt.name);

    return availableFilters
      .filter((flt) => !activeFilterNames.includes(flt.name))
      .map((flt) => ({
        value: flt.name,
        label: flt.label,
        description: flt.description
      }));
  }, [tableState.activeFilters, availableFilters]);

  const [selectedFilter, setSelectedFilter] = useState<string | null>(null);

  const valueOptions = useMemo(() => {
    // Find the matching filter
    let filter: TableFilter | undefined = availableFilters.find(
      (flt) => flt.name === selectedFilter
    );

    if (!filter) {
      return [];
    }

    switch (filter.type) {
      case 'boolean':
        return [
          { value: 'true', label: t`True` },
          { value: 'false', label: t`False` }
        ];
      default:
        return [];
    }
  }, [selectedFilter]);

  const setSelectedValue = useCallback(
    (value: string | null) => {
      // Find the matching filter
      let filter: TableFilter | undefined = availableFilters.find(
        (flt) => flt.name === selectedFilter
      );

      if (!filter) {
        return;
      }

      let filters = tableState.activeFilters.filter(
        (flt) => flt.name !== selectedFilter
      );

      let newFilter: TableFilter = {
        ...filter,
        value: value
      };

      tableState.setActiveFilters([...filters, newFilter]);
    },
    [selectedFilter]
  );

  return (
    <Stack spacing="xs">
      <Divider />
      <Select
        data={filterOptions}
        itemComponent={FilterSelectItem}
        searchable={true}
        placeholder={t`Select filter`}
        label={t`Filter`}
        onChange={(value: string | null) => setSelectedFilter(value)}
      />
      {selectedFilter && (
        <Select
          data={valueOptions}
          label={t`Value`}
          placeholder={t`Select filter value`}
          onChange={(value: string | null) => setSelectedValue(value)}
        />
      )}
    </Stack>
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
  const [addFilter, setAddFilter] = useState<boolean>(false);

  return (
    <Drawer
      size="sm"
      position="right"
      withCloseButton={true}
      opened={opened}
      onClose={onClose}
      title={<StylishText size="lg">{t`Table Filters`}</StylishText>}
    >
      <Stack spacing="xs">
        <Divider />
        {tableState.activeFilters.map((f) => (
          <FilterItem flt={f} tableState={tableState} />
        ))}
        {tableState.activeFilters.length > 0 && <Divider />}
        {addFilter && (
          <Stack spacing="xs">
            <FilterAddGroup
              tableState={tableState}
              availableFilters={availableFilters}
            />
          </Stack>
        )}
        <Group position="center" p="xs">
          {addFilter ? (
            <Button
              onClick={() => setAddFilter(false)}
              color="orange"
              variant="subtle"
            >
              <Text>{t`Cancel`}</Text>
            </Button>
          ) : (
            <>
              {tableState.activeFilters.length > 0 && (
                <Button
                  onClick={tableState.clearActiveFilters}
                  color="red"
                  variant="subtle"
                >
                  <Text>{t`Clear all filters`}</Text>
                </Button>
              )}
              <Button
                onClick={() => setAddFilter(true)}
                color="green"
                variant="subtle"
              >
                <Text>{t`Add filter`}</Text>
              </Button>
            </>
          )}
        </Group>
      </Stack>
    </Drawer>
  );
}
