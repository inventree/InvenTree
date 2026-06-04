import { StylishText } from '@lib/components/StylishText';
import type {
  FilterSetState,
  TableFilter,
  TableFilterChoice,
  TableFilterType
} from '@lib/types/Filters';
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
  Space,
  Stack,
  Text,
  TextInput,
  Tooltip
} from '@mantine/core';
import { DateInput, type DateValue } from '@mantine/dates';
import { IconCheck } from '@tabler/icons-react';
import dayjs from 'dayjs';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { StylishText } from '@lib/components/StylishText';
import type {
  FilterSetState,
  TableFilter,
  TableFilterChoice,
  TableFilterType
} from '@lib/types/Filters';
import {
  IconCheck,
  IconFilterStar,
  IconReload,
  IconX
} from '@tabler/icons-react';
import { api } from '../App';
import { StandaloneField } from '../components/forms/StandaloneField';
import {
  filterDisplayLabel,
  filterDisplayValue,
  getTableFilterOptions
} from './Filter';

/*
 * Render a preview of a single filter
 */
export function FilterPreview({
  filter,
  filters
}: Readonly<{
  filter: TableFilter;
  filters?: TableFilter[];
}>) {
  return (
    <Group key={filter.name} justify='space-between' gap='xl' wrap='nowrap'>
      <Text size='sm'>
        {filter.label ?? filterDisplayLabel(filter.name, filters)}
      </Text>
      <Text size='xs'>
        {filter.displayValue ??
          filterDisplayValue(filter.name, filter.value, filters)}
      </Text>
    </Group>
  );
}

/*
 * Render a single table filter item
 */
function FilterItem({
  flt,
  filterSet,
  availableFilters
}: Readonly<{
  flt: TableFilter;
  filterSet: FilterSetState;
  availableFilters?: TableFilter[];
}>) {
  const removeFilter = useCallback(() => {
    const newFilters = filterSet.activeFilters.filter(
      (f) => f.name !== flt.name
    );
    filterSet.setActiveFilters(newFilters);
  }, [flt]);

  // Find the matching filter definition
  const filterProps: TableFilter | undefined = useMemo(() => {
    return availableFilters?.find((f) => f.name === flt.name);
  }, [availableFilters, flt]);

  return (
    <Paper p='sm' shadow='sm' radius='xs'>
      <Group justify='space-between' key={flt.name} wrap='nowrap'>
        <Stack gap='xs'>
          <Text size='sm'>{flt.label ?? filterProps?.label ?? flt.name}</Text>
          <Text size='xs'>{flt.description ?? filterProps?.description}</Text>
        </Stack>
        <Group justify='right'>
          <Badge>
            {flt.displayValue ??
              filterDisplayValue(flt.name, flt.value, availableFilters)}
          </Badge>
          <Tooltip
            label={t`Remove filter`}
            withinPortal={true}
            position='top-end'
          >
            <CloseButton size='md' c='red' onClick={removeFilter} />
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
            filters: filterProps.apiFilter,
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
          searchable={filterProps.type == 'choice'}
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
        ?.sort((a, b) => (a.label ?? a.name).localeCompare(b.label ?? b.name))
        ?.map((flt) => ({
          value: flt.name,
          label: flt.label ?? flt.name,
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

function SavedFilterSets({
  filterSet
}: Readonly<{
  filterSet: FilterSetState;
}>) {
  if (filterSet.savedFilterSets.length === 0) {
    return null;
  }

  return (
    <Stack gap='xs' justify='flex-end'>
      <Space h='md' />
      <StylishText size='md'>{t`Saved Filter Groups`}</StylishText>
      <Divider />
      <Stack gap='xs'>
        {filterSet.savedFilterSets.map((set) => (
          <Paper
            key={`filter-group-${set.name}`}
            p='sm'
            shadow='sm'
            radius='xs'
          >
            <Group justify='space-between' wrap='nowrap'>
              <Group gap='xs' wrap='nowrap'>
                <ActionIcon size='sm' variant='transparent'>
                  <IconFilterStar />
                </ActionIcon>
                <Text size='sm' style={{ flex: 1 }} truncate>
                  {set.name}
                </Text>
              </Group>
              <Group gap='xs' wrap='nowrap'>
                <Tooltip
                  label={t`Load filter group`}
                  withinPortal
                  position='top-end'
                >
                  <ActionIcon
                    size='sm'
                    variant='transparent'
                    color='green'
                    aria-label={`load-filter-group-${set.name}`}
                    onClick={() => filterSet.loadFilterSet(set.name)}
                  >
                    <IconReload />
                  </ActionIcon>
                </Tooltip>
                <Tooltip
                  label={t`Delete filter group`}
                  withinPortal
                  position='top-end'
                >
                  <ActionIcon
                    size='sm'
                    variant='transparent'
                    color='red'
                    aria-label={`delete-filter-group-${set.name}`}
                    onClick={() => filterSet.deleteFilterSet(set.name)}
                  >
                    <IconX style={{ transform: 'rotate(180deg)' }} />
                  </ActionIcon>
                </Tooltip>
              </Group>
            </Group>
          </Paper>
        ))}
      </Stack>
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
  const [saving, setSaving] = useState<boolean>(false);
  const [saveName, setSaveName] = useState<string>('');

  // Hide the "add filter" selection whenever the selected filters change
  useEffect(() => {
    setAddFilter(false);
  }, [filterSet.activeFilters]);

  const hasFilters: boolean = useMemo(() => {
    return (filterSet?.activeFilters ?? []).length > 0;
  }, [filterSet.activeFilters]);

  const confirmSave = useCallback(() => {
    const name = saveName.trim();
    if (name) {
      filterSet.saveFilterSet(name);
    }
    setSaveName('');
    setSaving(false);
  }, [saveName, filterSet]);

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
      styles={{ body: { height: '100%', overflow: 'hidden' } }}
    >
      <Divider />
      <Space h='sm' />
      <Stack gap='xs' justify='space-between'>
        <Stack gap='xs'>
          {hasFilters &&
            filterSet.activeFilters?.map((f) => (
              <FilterItem
                key={f.name}
                flt={f}
                filterSet={filterSet}
                availableFilters={availableFilters}
              />
            ))}
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
              variant='light'
            >
              <Text>{t`Cancel`}</Text>
            </Button>
          )}
          {!addFilter &&
            filterSet.activeFilters.length < availableFilters.length && (
              <Button
                onClick={() => setAddFilter(true)}
                color='green'
                variant='light'
              >
                <Text>{t`Add Filter`}</Text>
              </Button>
            )}
          {!addFilter && hasFilters && (
            <Button
              onClick={filterSet.clearActiveFilters}
              color='red'
              variant='light'
            >
              <Text>{t`Clear Filters`}</Text>
            </Button>
          )}
          {!addFilter &&
            hasFilters &&
            (saving ? (
              <Group gap='xs' wrap='nowrap'>
                <TextInput
                  style={{ flex: 1 }}
                  aria-label='filter-group-name'
                  placeholder={t`Group name`}
                  value={saveName}
                  onChange={(e) => setSaveName(e.currentTarget.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') confirmSave();
                    if (e.key === 'Escape') setSaving(false);
                  }}
                  autoFocus
                />
                <Tooltip label={t`Save`} withinPortal>
                  <ActionIcon
                    aria-label='save-filter-set'
                    color='green'
                    size='sm'
                    variant='transparent'
                    onClick={confirmSave}
                    disabled={!saveName.trim()}
                  >
                    <IconCheck />
                  </ActionIcon>
                </Tooltip>
                <Tooltip label={t`Cancel`} withinPortal>
                  <ActionIcon
                    aria-label='cancel-save-filter-set'
                    color='red'
                    size='sm'
                    variant='transparent'
                    onClick={() => setSaving(false)}
                  >
                    <IconX />
                  </ActionIcon>
                </Tooltip>
              </Group>
            ) : (
              <Button
                color='blue'
                variant='light'
                onClick={() => setSaving(true)}
              >
                <Text>{t`Save current filters`}</Text>
              </Button>
            ))}
        </Stack>
        <Stack gap='xs'>
          <SavedFilterSets filterSet={filterSet} />
          <Space h='sm' />
        </Stack>
      </Stack>
    </Drawer>
  );
}
