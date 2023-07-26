import { t } from '@lingui/macro';
import { Modal, Space } from '@mantine/core';
import { Select } from '@mantine/core';
import { Stack } from '@mantine/core';
import { Button, Group, Text } from '@mantine/core';
import { useMemo, useState } from 'react';

import { TableFilter } from './Filter';

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
    .map((flt) => ({ value: flt.name, label: flt.label }));

  return options;
}

/**
 * Modal dialog to add a new filter for a particular table
 * @param opened : boolean - Whether the modal is opened or not
 * @param onClose : () => void - Function called when the modal is closed
 * @returns
 */
export function FilterSelectModal({
  availableFilters,
  activeFilters,
  opened,
  onClose
}: {
  availableFilters: TableFilter[];
  activeFilters: TableFilter[];
  opened: boolean;
  onClose: () => void;
}) {
  let filterOptions = useMemo(
    () => constructAvailableFilters(activeFilters, availableFilters),
    [activeFilters, availableFilters]
  );

  return (
    <Modal title={t`Add Table Filter`} opened={opened} onClose={onClose}>
      <Stack>
        <Text>{t`Select from the available filters`}</Text>
        <Select
          data={filterOptions}
          label={t`Filter`}
          placeholder={t`Select filter`}
          searchable={true}
          onChange={(value) => console.log(value)}
        />
        <Select
          data={[]}
          disabled={true}
          label={t`Value`}
          placeholder={t`Select filter value`}
        />
        <Group position="right">
          <Button color="red" onClick={onClose}>{t`Cancel`}</Button>
          <Space />
          <Button color="green" onClick={onClose}>{t`Add Filter`}</Button>
        </Group>
      </Stack>
    </Modal>
  );
}
