import { t } from '@lingui/core/macro';
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

import type {
  FilterSetState,
  TableFilter,
  TableFilterChoice,
  TableFilterType
} from '@lib/types/Filters';
import { IconCheck } from '@tabler/icons-react';
import { StandaloneField } from '../components/forms/StandaloneField';
import { StylishText } from '../components/items/StylishText';
import { getTableFilterOptions } from './Filter';

/*
 * Render a single table filter item
 */
function FilterItem({
  flt,
  filterSet
}: Readonly<{
  flt: TableFilter;
  filterSet: FilterSetState;
}>) {
  const removeFilter = useCallback(() => {
    const newFilters = filterSet.activeFilters.filter(
      (f) => f.name !== flt.name
    );
    filterSet.setActiveFilters(newFilters);
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
  filterName,
  filterProps,
  valueOptions,
  onValueChange
}: {
  filterName: string;
  filterProps: TableFilter;
  valueOptions: TableFilterChoice[];
  onValueChange: (value: string | null, displayValue?: any) => void;
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

  switch (filterProps.type) {
    case 'api':
      return (
        <StandaloneField
          fieldName={`filter-${filterName}`}
          fieldDefinition={{
            field_type: 'related field',
            api_url: filterProps.apiUrl,
            placeholder: t`Select filter value`,
            model: filterProps.model,
            label: t`Select filter value`,
            onValueChange: (value: any, instance: any) => {
              onValueChange(value, filterProps.modelRenderer?.(instance));
            }
          }}
        />
      );
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
          searchable={true}
          label={t`Value`}
          withScrollArea={false}
          placeholder={t`Select filter value`}
          onChange={(value: string | null) => onValueChange(value)}
          maxDropdownHeight={800}
        />
      );
  }
}

function FilterAddGroup({
  filterSet,
  availableFilters
}: Readonly<{
  filterSet: FilterSetState;
  availableFilters: TableFilter[];
}>) {
  const filterOptions: TableFilterChoice[] = useMemo(() => {
    // List of filter names which are already active on this table
    let activeFilterNames: string[] = [];

    if (filterSet.activeFilters && filterSet.activeFilters.length > 0) {
      activeFilterNames = filterSet.activeFilters?.map((flt) => flt.name) ?? [];
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
  }, [filterSet.activeFilters, availableFilters]);

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

  // Determine the filter "type" - if it is not supplied
  const getFilterType = (filter: TableFilter): TableFilterType => {
    if (filter.type) {
      return filter.type;
    } else if (filter.apiUrl && filter.model) {
      return 'api';
    } else if (filter.choices || filter.choiceFunction) {
      return 'choice';
    } else {
      return 'boolean';
    }
  };

  // Extract filter definition
  const filterProps: TableFilter | undefined = useMemo(() => {
    const filter = availableFilters?.find((flt) => flt.name === selectedFilter);

    if (filter) {
      filter.type = getFilterType(filter);
    }

    return filter;
  }, [availableFilters, selectedFilter]);

  const setSelectedValue = useCallback(
    (value: string | null, displayValue?: any) => {
      // Find the matching filter
      const filter: TableFilter | undefined = availableFilters.find(
        (flt) => flt.name === selectedFilter
      );

      if (!filter) {
        return;
      }

      const filters =
        filterSet.activeFilters?.filter((flt) => flt.name !== selectedFilter) ??
        [];

      const newFilter: TableFilter = {
        ...filter,
        value: value,
        displayValue:
          displayValue ?? valueOptions.find((v) => v.value === value)?.label
      };

      filterSet.setActiveFilters([...filters, newFilter]);

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
        maxDropdownHeight={400}
      />
      {selectedFilter && filterProps && (
        <FilterElement
          filterName={selectedFilter}
          filterProps={filterProps}
          valueOptions={valueOptions}
          onValueChange={setSelectedValue}
        />
      )}
    </Stack>
  );
}

export function FilterSelectDrawer({
  title,
  availableFilters,
  filterSet,
  opened,
  onClose
}: Readonly<{
  title?: string;
  availableFilters: TableFilter[];
  filterSet: FilterSetState;
  opened: boolean;
  onClose: () => void;
}>) {
  const [addFilter, setAddFilter] = useState<boolean>(false);

  // Hide the "add filter" selection whenever the selected filters change
  useEffect(() => {
    setAddFilter(false);
  }, [filterSet.activeFilters]);

  const hasFilters: boolean = useMemo(() => {
    const filters = filterSet?.activeFilters ?? [];

    return filters.length > 0;
  }, [filterSet.activeFilters]);

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
      title={<StylishText size='lg'>{title ?? t`Table Filters`}</StylishText>}
    >
      <Stack gap='xs'>
        {hasFilters &&
          filterSet.activeFilters?.map((f) => (
            <FilterItem key={f.name} flt={f} filterSet={filterSet} />
          ))}
        {hasFilters && <Divider />}
        {addFilter && (
          <Stack gap='xs'>
            <FilterAddGroup
              filterSet={filterSet}
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
          filterSet.activeFilters.length < availableFilters.length && (
            <Button
              onClick={() => setAddFilter(true)}
              color='green'
              variant='subtle'
            >
              <Text>{t`Add Filter`}</Text>
            </Button>
          )}
        {!addFilter && filterSet.activeFilters.length > 0 && (
          <Button
            onClick={filterSet.clearActiveFilters}
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
