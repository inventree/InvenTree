import { t } from '@lingui/macro';
import {
  ActionIcon,
  Chip,
  CloseButton,
  Indicator,
  Space,
  Stack,
  Table,
  Text,
  Tooltip,
  filterProps
} from '@mantine/core';
import { Group } from '@mantine/core';
import { IconFilter, IconRefresh } from '@tabler/icons-react';
import { IconBarcode, IconPrinter } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { DataTable, DataTableSortStatus } from 'mantine-datatable';
import { useEffect, useState } from 'react';

import { api } from '../../App';
import { notYetImplemented } from '../../functions/notifications';
import { ButtonMenu } from '../items/ButtonMenu';
import { TableColumn } from './Column';
import { TableColumnSelect } from './ColumnSelect';
import { DownloadAction } from './DownloadAction';
import { TableFilter } from './Filter';
import { FilterGroup } from './FilterGroup';
import { TableSearchInput } from './Search';

/**
 * Table Component which extends DataTable with custom InvenTree functionality
 */

export function InvenTreeTable({
  url,
  params,
  columns,
  enableDownload = false,
  enableFilters = true,
  enablePagination = true,
  enableRefresh = true,
  enableSearch = true,
  enableSelection = false,
  pageSize = 25,
  tableKey = '',
  defaultSortColumn = '',
  noRecordsText = t`No records found`,
  printingActions = [],
  barcodeActions = [],
  customActionGroups = [],
  customFilters = []
}: {
  url: string;
  params: any;
  columns: TableColumn[];
  tableKey: string;
  defaultSortColumn?: string;
  noRecordsText?: string;
  enableDownload?: boolean;
  enableFilters?: boolean;
  enableSelection?: boolean;
  enableSearch?: boolean;
  enablePagination?: boolean;
  enableRefresh?: boolean;
  pageSize?: number;
  printingActions?: any[];
  barcodeActions?: any[];
  customActionGroups?: any[];
  customFilters?: TableFilter[];
}) {
  // Check if any columns are switchable (can be hidden)
  const hasSwitchableColumns = columns.some((col: any) => col.switchable);

  // Check if custom filtering is enabled for this table
  const hasCustomFilters = enableFilters && customFilters.length > 0;

  // Pagination
  const [page, setPage] = useState(1);

  // Filter list visibility
  const [filtersVisible, setFiltersVisible] = useState<boolean>(false);

  // Map of currently active filters, {name: value}
  const [activeFilters, setActiveFilters] = useState<any>({});

  // Data columns
  const [dataColumns, setDataColumns] = useState<any[]>(columns);

  // List of hidden columns
  let hiddenColumns = [];

  // Search term
  const [searchTerm, setSearchTerm] = useState<string>('');

  let latestSearchTerm = '';

  useEffect(() => {
    // Keep a shadow copy of the state variable, so that we can update it asynchronously
    latestSearchTerm = searchTerm;

    loadHiddenColumns();
    loadActiveFilters();
  }, [searchTerm]);

  // Load list of hidden columns from local storage
  function loadHiddenColumns() {
    hiddenColumns = JSON.parse(
      localStorage.getItem(`hidden-table-columns-${tableKey}`) || '[]'
    );

    // Update column visibility
    let newColumns = [...dataColumns];

    for (let idx = 0; idx < newColumns.length; idx++) {
      newColumns[idx].hidden = hiddenColumns.includes(newColumns[idx].accessor);
    }

    setDataColumns(newColumns);
  }

  // Load list of active filters from local storage
  function loadActiveFilters() {
    // TODO
  }

  // Callback when search term is updated
  function updateSearchTerm(term: string) {
    term = term.trim();
    // Ignore identical search terms
    if (term == searchTerm) return;

    setSearchTerm(term);
    latestSearchTerm = term;
    refetch();
  }

  // Data download callback
  function downloadData(fileFormat: string) {
    console.log('download data: ' + fileFormat);
  }

  // Data Sorting
  const [sortStatus, setSortStatus] = useState<DataTableSortStatus>({
    columnAccessor: defaultSortColumn,
    direction: 'asc'
  });

  // Return the ordering parameter
  function getOrderingTerm() {
    let key = sortStatus.columnAccessor;

    // Sorting column not specified
    if (key == '') {
      return '';
    }

    // Find matching column:
    // If column provides custom ordering term, use that
    let column = dataColumns.find((col) => col.accessor == key);
    return column?.ordering || key;
  }

  // Missing records text (based on server response)
  const [missingRecordsText, setMissingRecordsText] =
    useState<string>(noRecordsText);

  // Data selection
  const [selectedRecords, setSelectedRecords] = useState<any[]>([]);

  function onSelectedRecordsChange(records: any[]) {
    setSelectedRecords(records);
  }

  const handleSortStatusChange = (status: DataTableSortStatus) => {
    setPage(1);
    setSortStatus(status);
  };

  // Callback when column visibility is toggled
  function toggleColumn(columnName: string) {
    let newColumns = [...dataColumns];

    let hiddenColumns = [];

    // Toggle selected column
    for (let idx = 0; idx < newColumns.length; idx++) {
      if (newColumns[idx].accessor == columnName) {
        newColumns[idx].hidden = !newColumns[idx].hidden;
      }

      if (newColumns[idx].hidden) {
        hiddenColumns.push(newColumns[idx].accessor);
      }
    }

    // Save list of hidden columns to local storage
    localStorage.setItem(
      `hidden-table-columns-${tableKey}`,
      JSON.stringify(hiddenColumns)
    );

    // Refresh state
    setDataColumns(newColumns);
  }

  // Function to perform API query to fetch required data
  const fetchTableData = async () => {
    let queryParams = { ...params };

    // Handle pagination
    if (enablePagination) {
      queryParams.limit = pageSize;
      queryParams.offset = (page - 1) * pageSize;
    }

    // Handle custom search term
    if (latestSearchTerm) {
      queryParams.search = latestSearchTerm;
    }

    // Handle sorting
    let ordering = getOrderingTerm();
    if (sortStatus.direction == 'asc') {
      queryParams.ordering = ordering;
    } else {
      queryParams.ordering = `-${ordering}`;
    }

    return api
      .get(`http://localhost:8000/api/${url}`, {
        // TODO: Don't hardcode the base URL here!
        params: queryParams,
        timeout: 30 * 1000
      })
      .then(function (response) {
        switch (response.status) {
          case 200:
            setMissingRecordsText(noRecordsText);
            return response.data;
          case 400:
            setMissingRecordsText(t`Bad request`);
            break;
          case 401:
            setMissingRecordsText(t`Unauthorized`);
            break;
          case 403:
            setMissingRecordsText(t`Forbidden`);
            break;
          case 404:
            setMissingRecordsText(t`Not found`);
            break;
          default:
            setMissingRecordsText(
              t`Unknown error` + ': ' + response.statusText
            ); // TODO: Translate
            break;
        }

        return [];
      })
      .catch(function (error) {
        setMissingRecordsText(t`Error` + ': ' + error.message);
        return [];
      });
  };

  const { data, isError, isFetching, isLoading, refetch } = useQuery(
    [
      `table-${tableKey}`,
      sortStatus.columnAccessor,
      sortStatus.direction,
      page
    ],
    async () => fetchTableData(),
    {
      refetchOnWindowFocus: false,
      refetchOnMount: 'always'
    }
  );

  // Launch a modal dialog to add a new filter
  function onFilterAdd() {
    // TODO
    notYetImplemented();
  }

  return (
    <Stack>
      <Group position="apart">
        <Group position="left" spacing={5}>
          {customActionGroups.map((group: any, idx: number) => group)}
          {barcodeActions.length > 0 && (
            <ButtonMenu
              icon={<IconBarcode />}
              label={t`Barcode actions`}
              tooltip={t`Barcode actions`}
              actions={barcodeActions}
            />
          )}
          {printingActions.length > 0 && (
            <ButtonMenu
              icon={<IconPrinter />}
              label={t`Print actions`}
              tooltip={t`Print actions`}
              actions={printingActions}
            />
          )}
          {enableDownload && <DownloadAction downloadCallback={downloadData} />}
        </Group>
        <Space />
        <Group position="right" spacing={5}>
          {enableSearch && (
            <TableSearchInput
              searchCallback={(term: string) => updateSearchTerm(term)}
            />
          )}
          {enableRefresh && (
            <ActionIcon>
              <Tooltip label={t`Refresh data`}>
                <IconRefresh onClick={() => refetch()} />
              </Tooltip>
            </ActionIcon>
          )}
          {hasSwitchableColumns && (
            <TableColumnSelect
              columns={dataColumns}
              onToggleColumn={toggleColumn}
            />
          )}
          {hasCustomFilters && (
            <Indicator
              size="xs"
              label={activeFilters.length}
              disabled={activeFilters.length == 0}
            >
              <ActionIcon>
                <Tooltip label={t`Filter data`}>
                  <IconFilter
                    onClick={() => setFiltersVisible(!filtersVisible)}
                  />
                </Tooltip>
              </ActionIcon>
            </Indicator>
          )}
        </Group>
      </Group>
      {filtersVisible && (
        <FilterGroup
          filterList={[]}
          onFilterAdd={onFilterAdd}
          onFilterRemove={notYetImplemented}
          onFilterClearAll={notYetImplemented}
        />
      )}
      <DataTable
        withBorder
        striped
        highlightOnHover
        loaderVariant="dots"
        idAccessor={'pk'}
        minHeight={200}
        totalRecords={data?.count ?? data?.length ?? 0}
        recordsPerPage={pageSize}
        page={page}
        onPageChange={setPage}
        sortStatus={sortStatus}
        onSortStatusChange={handleSortStatusChange}
        selectedRecords={enableSelection ? selectedRecords : undefined}
        onSelectedRecordsChange={
          enableSelection ? onSelectedRecordsChange : undefined
        }
        fetching={isFetching}
        noRecordsText={missingRecordsText}
        records={data?.results ?? data ?? []}
        columns={dataColumns}
      />
    </Stack>
  );
}
