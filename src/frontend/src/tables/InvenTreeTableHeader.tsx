import { t } from '@lingui/core/macro';
import {
  ActionIcon,
  Alert,
  Divider,
  Group,
  HoverCard,
  Indicator,
  Paper,
  Space,
  Stack,
  Text,
  Tooltip
} from '@mantine/core';
import {
  IconBarcode,
  IconDownload,
  IconExclamationCircle,
  IconFilter,
  IconRefresh,
  IconTrash
} from '@tabler/icons-react';
import { useMemo, useState } from 'react';
import { Fragment } from 'react/jsx-runtime';

import { ActionButton } from '@lib/components/ActionButton';
import { ButtonMenu } from '@lib/components/ButtonMenu';
import { SearchInput } from '@lib/components/SearchInput';
import { resolveItem } from '@lib/functions/Conversion';
import type { TableFilter } from '@lib/types/Filters';
import type { TableState } from '@lib/types/Tables';
import type { InvenTreeTableProps } from '@lib/types/Tables';
import { showNotification } from '@mantine/notifications';
import { Boundary } from '../components/Boundary';
import { PrintingActions } from '../components/buttons/PrintingActions';
import { StylishText } from '../components/items/StylishText';
import useDataExport from '../hooks/UseDataExport';
import { useDeleteApiFormModal } from '../hooks/UseForm';
import { TableColumnSelect } from './ColumnSelect';
import { FilterSelectDrawer } from './FilterSelectDrawer';

/**
 * Render a composite header for an InvenTree table
 */
export default function InvenTreeTableHeader({
  tableUrl,
  tableState,
  tableProps,
  hasSwitchableColumns,
  columns,
  filters,
  toggleColumn
}: Readonly<{
  tableUrl?: string;
  tableState: TableState;
  tableProps: InvenTreeTableProps<any>;
  hasSwitchableColumns: boolean;
  columns: any;
  filters: TableFilter[];
  toggleColumn: (column: string) => void;
}>) {
  // Filter list visibility
  const [filtersVisible, setFiltersVisible] = useState<boolean>(false);

  // Construct export filters
  const exportFilters = useMemo(() => {
    const filters: Record<string, any> = {};

    // Add in any additional parameters which have a defined value
    for (const [key, value] of Object.entries(tableProps.params ?? {})) {
      if (value != undefined) {
        filters[key] = value;
      }
    }

    // Add in active filters
    if (tableState.filterSet.activeFilters) {
      tableState.filterSet.activeFilters.forEach((filter) => {
        filters[filter.name] = filter.value;
      });
    }

    // Allow overriding of query parameters
    if (tableState.queryFilters) {
      for (const [key, value] of tableState.queryFilters) {
        if (value != undefined) {
          filters[key] = value;
        }
      }
    }

    return filters;
  }, [tableProps.params, tableState.filterSet, tableState.queryFilters]);

  const exportModal = useDataExport({
    url: tableUrl ?? '',
    enabled: !!tableUrl && tableProps?.enableDownload != false,
    filters: exportFilters,
    searchTerm: tableState.searchTerm
  });

  const deleteRecords = useDeleteApiFormModal({
    url: tableUrl ?? '',
    title: t`Delete Selected Items`,
    preFormContent: (
      <Alert
        color='red'
        title={t`Are you sure you want to delete the selected items?`}
      >
        {t`This action cannot be undone`}
      </Alert>
    ),
    initialData: {
      items: tableState.selectedIds
    },
    fields: {
      items: {
        hidden: true
      }
    },
    successMessage: t`Items deleted`,
    onFormError: (response) => {
      showNotification({
        id: 'bulk-delete-error',
        title: t`Error`,
        message: t`Failed to delete items`,
        color: 'red',
        icon: <IconExclamationCircle />,
        autoClose: 5000
      });
    },
    onFormSuccess: () => {
      tableState.clearSelectedRecords();
      tableState.refreshTable();

      if (tableProps.afterBulkDelete) {
        tableProps.afterBulkDelete();
      }
    }
  });

  const hasCustomSearch = useMemo(() => {
    return tableState.queryFilters.has('search');
  }, [tableState.queryFilters]);

  const hasCustomFilters = useMemo(() => {
    return (tableState?.queryFilters?.size ?? 0) > 0;
  }, [tableState.queryFilters]);

  // Extract ID values for label and report printing
  const printingIdValues = useMemo(() => {
    return (
      tableState.selectedRecords?.map((record) => {
        return resolveItem(record, tableProps.printingAccessor ?? 'pk');
      }) ?? []
    );
  }, [tableProps.printingAccessor, tableState.selectedRecords]);

  return (
    <>
      {exportModal.modal}
      {deleteRecords.modal}
      {tableProps.enableFilters && (filters.length ?? 0) > 0 && (
        <Boundary label={`InvenTreeTableFilterDrawer-${tableState.tableKey}`}>
          <FilterSelectDrawer
            availableFilters={filters}
            filterSet={tableState.filterSet}
            opened={filtersVisible}
            onClose={() => setFiltersVisible(false)}
          />
        </Boundary>
      )}
      {(hasCustomFilters || hasCustomSearch) && (
        <Alert
          color='yellow'
          withCloseButton
          title={t`Custom table filters are active`}
          onClose={() => tableState.clearQueryFilters()}
        />
      )}
      <Group justify='apart' grow wrap='nowrap'>
        <Group justify='left' key='custom-actions' gap={5} wrap='nowrap'>
          <PrintingActions
            items={printingIdValues}
            modelType={tableProps.modelType}
            enableLabels={tableProps.enableLabels}
            enableReports={tableProps.enableReports}
          />
          {(tableProps.barcodeActions?.length ?? 0) > 0 && (
            <ButtonMenu
              key='barcode-actions'
              icon={<IconBarcode />}
              label={t`Barcode Actions`}
              tooltip={t`Barcode Actions`}
              actions={tableProps.barcodeActions ?? []}
            />
          )}
          {tableProps.enableBulkDelete && (
            <ActionButton
              disabled={!tableState.hasSelectedRecords}
              icon={<IconTrash />}
              color='red'
              tooltip={t`Delete selected records`}
              onClick={() => {
                deleteRecords.open();
              }}
            />
          )}
          {tableProps.tableActions?.map((group, idx) => (
            <Fragment key={idx}>{group}</Fragment>
          ))}
        </Group>
        <Space />
        <Group justify='right' gap={5} wrap='nowrap'>
          {tableProps.enableSearch && (
            <SearchInput
              disabled={hasCustomSearch}
              searchCallback={(term: string) => tableState.setSearchTerm(term)}
            />
          )}
          {tableProps.enableRefresh && (
            <ActionIcon variant='transparent' aria-label='table-refresh'>
              <Tooltip label={t`Refresh data`} position='top-end'>
                <IconRefresh
                  onClick={() => {
                    tableState.refreshTable();
                    tableState.clearSelectedRecords();
                  }}
                />
              </Tooltip>
            </ActionIcon>
          )}
          {hasSwitchableColumns && (
            <TableColumnSelect
              columns={columns}
              onToggleColumn={toggleColumn}
            />
          )}
          {tableProps.enableFilters && filters.length > 0 && (
            <Indicator
              size='xs'
              label={tableState.filterSet.activeFilters?.length ?? 0}
              disabled={tableState.filterSet.activeFilters?.length == 0}
            >
              <ActionIcon
                disabled={hasCustomFilters}
                variant='transparent'
                aria-label='table-select-filters'
              >
                <HoverCard
                  position='bottom-end'
                  withinPortal={true}
                  disabled={
                    hasCustomFilters ||
                    !tableState.filterSet.activeFilters?.length
                  }
                >
                  <HoverCard.Target>
                    <Tooltip
                      label={t`Table Filters`}
                      position='top-end'
                      disabled={!!tableState.filterSet.activeFilters?.length}
                    >
                      <IconFilter
                        onClick={() => setFiltersVisible(!filtersVisible)}
                      />
                    </Tooltip>
                  </HoverCard.Target>
                  <HoverCard.Dropdown>
                    <Paper p='sm' withBorder>
                      <Stack gap='xs'>
                        <StylishText size='md'>{t`Active Filters`}</StylishText>
                        <Divider />
                        {tableState.filterSet.activeFilters?.map((filter) => (
                          <Group
                            key={filter.name}
                            justify='space-between'
                            gap='xl'
                            wrap='nowrap'
                          >
                            <Text size='sm'>{filter.label}</Text>
                            <Text size='xs'>{filter.displayValue}</Text>
                          </Group>
                        ))}
                      </Stack>
                    </Paper>
                  </HoverCard.Dropdown>
                </HoverCard>
              </ActionIcon>
            </Indicator>
          )}
          {tableUrl && tableProps.enableDownload && (
            <ActionIcon variant='transparent' aria-label='table-export-data'>
              <Tooltip label={t`Export data`} position='top-end'>
                <IconDownload onClick={exportModal.open} />
              </Tooltip>
            </ActionIcon>
          )}
        </Group>
      </Group>
    </>
  );
}
