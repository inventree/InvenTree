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
  IconDownload,
  IconFilter,
  IconRefresh,
  IconTrash
} from '@tabler/icons-react';
import { useMemo, useState } from 'react';
import { Fragment } from 'react/jsx-runtime';

import { useQuery } from '@tanstack/react-query';
import { Boundary } from '../components/Boundary';
import { ActionButton } from '../components/buttons/ActionButton';
import { ButtonMenu } from '../components/buttons/ButtonMenu';
import { PrintingActions } from '../components/buttons/PrintingActions';
import type { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';
import { useApi } from '../contexts/ApiContext';
import { extractAvailableFields } from '../functions/forms';
import { generateUrl } from '../functions/urls';
import { useCreateApiFormModal, useDeleteApiFormModal } from '../hooks/UseForm';
import type { TableState } from '../hooks/UseTable';
import { TableColumnSelect } from './ColumnSelect';
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

  // Selected plugin to use for data export
  const [pluginKey, setPluginKey] = useState<string>('inventree-exporter');

  // Construct the URL for the export request
  const exportParams = useMemo(() => {
    const queryParams = {
      ...tableProps.params,
      export: true,
      export_plugin: pluginKey || undefined
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

    return queryParams;
  }, [
    pluginKey,
    tableUrl,
    tableProps.params,
    tableState.activeFilters,
    tableState.queryFilters,
    tableState.searchTerm
  ]);

  // Fetch available export fields via OPTIONS request
  const extraExportFields = useQuery({
    enabled: !!tableUrl && tableProps.enableDownload,
    queryKey: ['exportFields', pluginKey, tableUrl, exportParams],
    gcTime: 500,
    queryFn: () =>
      api
        .options(tableUrl ?? '', {
          params: exportParams
        })
        .then((response: any) => {
          return extractAvailableFields(response, 'POST') || {};
        })
        .catch(() => {
          return {};
        })
  });

  const exportFields: ApiFormFieldSet = useMemo(() => {
    const extraFields: ApiFormFieldSet = extraExportFields.data || {};

    const fields: ApiFormFieldSet = {
      export_format: {},
      export_plugin: {},
      ...extraFields
    };

    fields.export_plugin = {
      ...fields.export_plugin,
      onValueChange: (value: string) => {
        setPluginKey(value);
      }
    };

    return fields;
  }, [extraExportFields.data, setPluginKey]);

  const exportModal = useCreateApiFormModal({
    url: tableUrl ?? '',
    queryParams: new URLSearchParams(exportParams),
    title: t`Export Data`,
    fields: exportFields,
    submitText: t`Export`,
    successMessage: t`Data exported successfully`,
    onFormSuccess: (response: any) => {
      setPluginKey('');

      if (response.complete && response.output) {
        // Download the generated file
        const url = generateUrl(response.output);
        window.open(url.toString(), '_blank');
      }
    }
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
    onFormSuccess: () => {
      tableState.clearSelectedRecords();
      tableState.refreshTable();

      if (tableProps.afterBulkDelete) {
        tableProps.afterBulkDelete();
      }
    }
  });

  return (
    <>
      {exportModal.modal}
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
      {tableState.queryFilters.size > 0 && (
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
          {tableUrl && tableProps.enableDownload && (
            <ActionIcon variant='transparent' aria-label='export-data'>
              <Tooltip label={t`Download data`} position='bottom'>
                <IconDownload onClick={exportModal.open} />
              </Tooltip>
            </ActionIcon>
          )}
        </Group>
      </Group>
    </>
  );
}
