import { t } from '@lingui/macro';
import {
  ActionIcon,
  Badge,
  Button,
  CloseButton,
  Divider,
  Drawer,
  Group,
  Paper,
  Select,
  Stack,
  Text,
  TextInput,
  Tooltip
} from '@mantine/core';
import { DateInput, type DateValue } from '@mantine/dates';
import dayjs from 'dayjs';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { IconCheck } from '@tabler/icons-react';
import { StylishText } from '../components/items/StylishText';
import type { TableState } from '../hooks/UseTable';
import {
  type TableFilter,
  type TableFilterChoice,
  type TableFilterType,
  getTableFilterOptions
} from './Filter';

/*
 * Render a single table filter item
 */
function FilterItem({
  flt,
  tableState
}: Readonly<{
  flt: TableFilter;
  tableState: TableState;
}>) {
  const removeFilter = useCallback(() => {
    const newFilters = tableState.activeFilters.filter(
      (f) => f.name !== flt.name
    );
    tableState.setActiveFilters(newFilters);
  }, [flt]);

  return (
    <Paper p='sm' shadow='sm' radius='xs'>
      <Group justify='space-between' key={flt.name} wrap='nowrap'>
        <Stack gap='xs'>
          <Text size='sm'>{flt.label}</Text>
          <Text size='xs'>{flt.description}</Text>
        </Stack>
        <Group justify='right'>
          <Badge>{flt.displayValue ?? flt.value}</Badge>
          <Tooltip label={t`Remove filter`} withinPortal={true}>
            <CloseButton size='md' color='red' onClick={removeFilter} />
          </Tooltip>
        </Group>
      </Group>
    </Paper>
  );
}

function FilterElement({
  filterType,
  valueOptions,
  onValueChange
}: {
  filterType: TableFilterType;
  valueOptions: TableFilterChoice[];
  onValueChange: (value: string | null) => void;
}) {
  const setDateValue = useCallback(
    (value: DateValue) => {
      if (value) {
        const date = value.toString();
        onValueChange(dayjs(date).format('YYYY-MM-DD'));
      } else {
        onValueChange('');
      }
    },
    [onValueChange]
  );

  const [textValue, setTextValue] = useState<string>('');

  switch (filterType) {
    case 'text':
      return (
        <TextInput
          label={t`Value`}
          value={textValue}
          placeholder={t`Enter filter value`}
          rightSection={
            <ActionIcon
              aria-label='apply-text-filter'
              variant='transparent'
              onClick={() => onValueChange(textValue)}
            >
              <IconCheck />
            </ActionIcon>
          }
          onChange={(e) => setTextValue(e.currentTarget.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              onValueChange(textValue);
            }
          }}
        />
      );
    case 'date':
      return (
        <DateInput
          label={t`Value`}
          placeholder={t`Select date value`}
          onChange={setDateValue}
        />
      );
    case 'choice':
    case 'boolean':
    default:
      return (
        <Select
          data={valueOptions}
          searchable={filterType != 'boolean'}
          label={t`Value`}
          placeholder={t`Select filter value`}
          onChange={(value: string | null) => onValueChange(value)}
          maxDropdownHeight={800}
        />
      );
  }
}

function FilterAddGroup({
  tableState,
  availableFilters
}: Readonly<{
  tableState: TableState;
  availableFilters: TableFilter[];
}>) {
  const filterOptions: TableFilterChoice[] = useMemo(() => {
    // List of filter names which are already active on this table
    let activeFilterNames: string[] = [];

    if (tableState.activeFilters && tableState.activeFilters.length > 0) {
      activeFilterNames =
        tableState.activeFilters?.map((flt) => flt.name) ?? [];
    }

    return (
      availableFilters
        ?.filter((flt) => !activeFilterNames.includes(flt.name))
        ?.sort((a, b) => a.label.localeCompare(b.label))
        ?.map((flt) => ({
          value: flt.name,
          label: flt.label,
          description: flt.description
        })) ?? []
    );
  }, [tableState.activeFilters, availableFilters]);

  const [selectedFilter, setSelectedFilter] = useState<string | null>(null);

  const valueOptions: TableFilterChoice[] = useMemo(() => {
    // Find the matching filter
    const filter: TableFilter | undefined = availableFilters?.find(
      (flt) => flt.name === selectedFilter
    );

    if (!filter) {
      return [];
    }

    return getTableFilterOptions(filter);
  }, [selectedFilter]);

  // Determine the "type" of filter (default = boolean)
  const filterType: TableFilterType = useMemo(() => {
    const filter = availableFilters?.find((flt) => flt.name === selectedFilter);

    if (filter?.type) {
      return filter.type;
    } else if (filter?.choices) {
      // If choices are provided, it is a choice filter
      return 'choice';
    } else {
      // Default fallback
      return 'boolean';
    }
  }, [selectedFilter]);

  const setSelectedValue = useCallback(
    (value: string | null) => {
      // Find the matching filter
      const filter: TableFilter | undefined = availableFilters.find(
        (flt) => flt.name === selectedFilter
      );

      if (!filter) {
        return;
      }

      const filters =
        tableState.activeFilters?.filter(
          (flt) => flt.name !== selectedFilter
        ) ?? [];

      const newFilter: TableFilter = {
        ...filter,
        value: value,
        displayValue: valueOptions.find((v) => v.value === value)?.label
      };

      tableState.setActiveFilters([...filters, newFilter]);

      // Clear selected filter
      setSelectedFilter(null);
    },
    [selectedFilter]
  );

  return (
    <Stack gap='xs'>
      <Divider />
      <Select
        data={filterOptions}
        searchable={true}
        placeholder={t`Select filter`}
        label={t`Filter`}
        onChange={(value: string | null) => setSelectedFilter(value)}
        maxDropdownHeight={800}
      />
      {selectedFilter && (
        <FilterElement
          filterType={filterType}
          valueOptions={valueOptions}
          onValueChange={setSelectedValue}
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
}: Readonly<{
  availableFilters: TableFilter[];
  tableState: TableState;
  opened: boolean;
  onClose: () => void;
}>) {
  const [addFilter, setAddFilter] = useState<boolean>(false);

  // Hide the "add filter" selection whenever the selected filters change
  useEffect(() => {
    setAddFilter(false);
  }, [tableState.activeFilters]);

  const hasFilters: boolean = useMemo(() => {
    const filters = tableState?.activeFilters ?? [];

    return filters.length > 0;
  }, [tableState.activeFilters]);

  return (
    <Drawer
      size='sm'
      position='right'
      withCloseButton={true}
      opened={opened}
      onClose={onClose}
      closeButtonProps={{
        'aria-label': 'filter-drawer-close'
      }}
      title={<StylishText size='lg'>{t`Table Filters`}</StylishText>}
    >
      <Stack gap='xs'>
        {hasFilters &&
          tableState.activeFilters?.map((f) => (
            <FilterItem key={f.name} flt={f} tableState={tableState} />
          ))}
        {hasFilters && <Divider />}
        {addFilter && (
          <Stack gap='xs'>
            <FilterAddGroup
              tableState={tableState}
              availableFilters={availableFilters}
            />
          </Stack>
        )}
        {addFilter && (
          <Button
            onClick={() => setAddFilter(false)}
            color='orange'
            variant='subtle'
          >
            <Text>{t`Cancel`}</Text>
          </Button>
        )}
        {!addFilter &&
          tableState.activeFilters.length < availableFilters.length && (
            <Button
              onClick={() => setAddFilter(true)}
              color='green'
              variant='subtle'
            >
              <Text>{t`Add Filter`}</Text>
            </Button>
          )}
        {!addFilter && tableState.activeFilters.length > 0 && (
          <Button
            onClick={tableState.clearActiveFilters}
            color='red'
            variant='subtle'
          >
            <Text>{t`Clear Filters`}</Text>
          </Button>
        )}
      </Stack>
    </Drawer>
  );
}
