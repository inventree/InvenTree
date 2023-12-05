import { t } from '@lingui/macro';
import { Modal } from '@mantine/core';
import { Select } from '@mantine/core';
import { Stack } from '@mantine/core';
import { Button, Group, Text } from '@mantine/core';
import { forwardRef, useMemo, useState } from 'react';

import { TableFilter, TableFilterChoice } from './Filter';

/**
 * Construct the selection of filters
 */
function constructAvailableFilters(
  activeFilters: TableFilter[],
  availableFilters: TableFilter[]
) {
  // Collect a list of active filters
  let activeFilterNames = activeFilters.map((flt) => flt.name);

  let options = availableFilters
    .filter((flt) => !activeFilterNames.includes(flt.name))
    .map((flt) => ({
      value: flt.name,
      label: flt.label,
      description: flt.description
    }));

  return options;
}

/**
 * Construct the selection of available values for the selected filter
 */
function constructValueOptions(
  availableFilters: TableFilter[],
  selectedFilter: string | null
) {
  // No options if no filter is selected
  if (!selectedFilter) {
    return [];
  }

  let filter = availableFilters.find((flt) => flt.name === selectedFilter);

  if (!filter) {
    console.error(`Could not find filter ${selectedFilter}`);
    return [];
  }

  let options: TableFilterChoice[] = [];

  switch (filter.type) {
    case 'boolean':
      // Boolean filter values True / False
      options = [
        { value: 'true', label: t`True` },
        { value: 'false', label: t`False` }
      ];
      break;
    default:
      // Choices are supplied by the filter definition
      if (filter.choices) {
        options = filter.choices;
      } else if (filter.choiceFunction) {
        options = filter.choiceFunction();
      } else {
        console.error(`Filter choices not supplied for filter ${filter.name}`);
      }
      break;
  }

  return options;
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

/**
 * Modal dialog to add a} new filter for a particular table
 * @param opened : boolean - Whether the modal is opened or not
 * @param onClose : () => void - Function called when the modal is closed
 * @returns
 */
export function FilterSelectModal({
  availableFilters,
  activeFilters,
  opened,
  onCreateFilter,
  onClose
}: {
  availableFilters: TableFilter[];
  activeFilters: TableFilter[];
  opened: boolean;
  onCreateFilter: (name: string, value: string) => void;
  onClose: () => void;
}) {
  let filterOptions = useMemo(
    () => constructAvailableFilters(activeFilters, availableFilters),
    [activeFilters, availableFilters]
  );

  // Internal state variable for the selected filter
  let [selectedFilter, setSelectedFilter] = useState<string | null>(null);

  // Internal state variable for the selected filter value
  let [value, setValue] = useState<string | null>(null);

  let valueOptions = useMemo(
    () => constructValueOptions(availableFilters, selectedFilter),
    [availableFilters, activeFilters, selectedFilter]
  );

  // Callback when the modal is closed. Ensure that the internal state is reset
  function closeModal() {
    setSelectedFilter(null);
    setValue(null);
    onClose();
  }

  function createFilter() {
    if (selectedFilter && value) {
      onCreateFilter(selectedFilter, value);
    }
    closeModal();
  }

  return (
    <Modal title={t`Add Table Filter`} opened={opened} onClose={closeModal}>
      <Stack>
        <Text>{t`Select from the available filters`}</Text>
        <Select
          data={filterOptions}
          itemComponent={FilterSelectItem}
          label={t`Filter`}
          placeholder={t`Select filter`}
          searchable={true}
          onChange={(value) => setSelectedFilter(value)}
          withinPortal={true}
          maxDropdownHeight={400}
        />
        <Select
          data={valueOptions}
          disabled={valueOptions.length == 0}
          label={t`Value`}
          placeholder={t`Select filter value`}
          onChange={(value) => setValue(value)}
          withinPortal={true}
          maxDropdownHeight={400}
        />
        <Group position="right">
          <Button color="red" onClick={closeModal}>{t`Cancel`}</Button>
          <Button
            color="green"
            onClick={createFilter}
            disabled={!(selectedFilter && value)}
          >
            {t`Add Filter`}
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
