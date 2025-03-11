import { t } from '@lingui/macro';
import {
  ActionIcon,
  Alert,
  Group,
  Indicator,
  Space,
  Tooltip
} from '@mantine/core';
import {
  IconBarcode,
  IconFilter,
  IconRefresh,
  IconTrash
} from '@tabler/icons-react';
import { useMemo, useState } from 'react';
import { Fragment } from 'react/jsx-runtime';

import { Boundary } from '../components/Boundary';
import { ActionButton } from '../components/buttons/ActionButton';
import { ButtonMenu } from '../components/buttons/ButtonMenu';
import { PrintingActions } from '../components/buttons/PrintingActions';
import { useApi } from '../contexts/ApiContext';
import { useDeleteApiFormModal } from '../hooks/UseForm';
import type { TableState } from '../hooks/UseTable';
import { TableColumnSelect } from './ColumnSelect';
import { DownloadAction } from './DownloadAction';
import type { TableFilter } from './Filter';
import { FilterSelectDrawer } from './FilterSelectDrawer';
import type { InvenTreeTableProps } from './InvenTreeTable';
import { TableSearchInput } from './Search';

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
  const api = useApi();

  // Filter list visibility
  const [filtersVisible, setFiltersVisible] = useState<boolean>(false);

  const downloadData = (fileFormat: string) => {
    // Download entire dataset (no pagination)

    const queryParams = {
      ...tableProps.params
    };

    // Add in active filters
    if (tableState.activeFilters) {
      tableState.activeFilters.forEach((filter) => {
        queryParams[filter.name] = filter.value;
      });
    }

    // Allow overriding of query parameters
    if (tableState.queryFilters) {
      for (const [key, value] of tableState.queryFilters) {
        queryParams[key] = value;
      }
    }

    // Add custom search term
    if (tableState.searchTerm) {
      queryParams.search = tableState.searchTerm;
    }

    // Specify file format
    queryParams.export = fileFormat;

    const downloadUrl = api.getUri({
      url: tableUrl,
      params: queryParams
    });

    // Download file in a new window (to force download)
    window.open(downloadUrl, '_blank');
  };

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
    if (hasCustomSearch) {
      return tableState.queryFilters.size > 1;
    } else {
      return tableState.queryFilters.size > 0;
    }
  }, [hasCustomSearch, tableState.queryFilters]);

  return (
    <>
      {deleteRecords.modal}
      {tableProps.enableFilters && (filters.length ?? 0) > 0 && (
        <Boundary label={`InvenTreeTableFilterDrawer-${tableState.tableKey}`}>
          <FilterSelectDrawer
            availableFilters={filters}
            tableState={tableState}
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
            items={tableState.selectedIds}
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
            <TableSearchInput
              disabled={hasCustomSearch}
              searchCallback={(term: string) => tableState.setSearchTerm(term)}
            />
          )}
          {tableProps.enableRefresh && (
            <ActionIcon variant='transparent' aria-label='table-refresh'>
              <Tooltip label={t`Refresh data`}>
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
              label={tableState.activeFilters?.length ?? 0}
              disabled={tableState.activeFilters?.length == 0}
            >
              <ActionIcon
                disabled={hasCustomFilters}
                variant='transparent'
                aria-label='table-select-filters'
              >
                <Tooltip label={t`Table Filters`}>
                  <IconFilter
                    onClick={() => setFiltersVisible(!filtersVisible)}
                  />
                </Tooltip>
              </ActionIcon>
            </Indicator>
          )}
          {tableProps.enableDownload && (
            <DownloadAction
              key='download-action'
              downloadCallback={downloadData}
            />
          )}
        </Group>
      </Group>
    </>
  );
}
