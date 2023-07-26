import { t } from '@lingui/macro';
import { ActionIcon, Indicator, Space, Stack, Tooltip } from '@mantine/core';
import { Group } from '@mantine/core';
import { IconFilter, IconRefresh } from '@tabler/icons-react';
import { IconBarcode, IconPrinter } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { DataTable, DataTableSortStatus } from 'mantine-datatable';
import { useEffect, useState } from 'react';

import { api } from '../../App';
import { ButtonMenu } from '../items/ButtonMenu';
import { TableColumn } from './Column';
import { TableColumnSelect } from './ColumnSelect';
import { DownloadAction } from './DownloadAction';
import { TableFilter } from './Filter';
import { FilterGroup } from './FilterGroup';
import { FilterSelectModal } from './FilterSelectModal';
import { TableSearchInput } from './Search';

/*
 * Load list of hidden columns from local storage.
 * Returns a list of column names which are "hidden" for the current table
 */
function loadHiddenColumns(tableKey: string) {
  return JSON.parse(
    localStorage.getItem(`inventree-hidden-table-columns-${tableKey}`) || '[]'
  );
}

/**
 * Write list of hidden columns to local storage
 * @param tableKey : string - unique key for the table
 * @param columns : string[] - list of column names
 */
function saveHiddenColumns(tableKey: string, columns: any[]) {
  localStorage.setItem(
    `inventree-hidden-table-columns-${tableKey}`,
    JSON.stringify(columns)
  );
}

/**
 * Loads the list of active filters from local storage
 * @param tableKey : string - unique key for the table
 * @param filterList : TableFilter[] - list of available filters
 * @returns a map of active filters for the current table, {name: value}
 */
function loadActiveFilters(tableKey: string, filterList: TableFilter[]) {
  let active = JSON.parse(
    localStorage.getItem(`inventree-active-table-filters-${tableKey}`) || '{}'
  );

  // We expect that the active filter list is a map of {name: value}
  // Return *only* those filters which are in the filter list
  let x = filterList
    .filter((f) => f.name in active)
    .map((f) => ({
      ...f,
      value: active[f.name]
    }));

  return x;
}

/**
 * Write the list of active filters to local storage
 * @param tableKey : string - unique key for the table
 * @param filters : any - map of active filters, {name: value}
 */
function saveActiveFilters(tableKey: string, filters: TableFilter[]) {
  let active = Object.fromEntries(filters.map((flt) => [flt.name, flt.value]));

  localStorage.setItem(
    `inventree-active-table-filters-${tableKey}`,
    JSON.stringify(active)
  );
}

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
  // Data columns
  const [dataColumns, setDataColumns] = useState<any[]>(columns);

  // Check if any columns are switchable (can be hidden)
  const hasSwitchableColumns = columns.some((col: any) => col.switchable);

  // Manage state for switchable columns (initially load from local storage)
  let [hiddenColumns, setHiddenColumns] = useState(() =>
    loadHiddenColumns(tableKey)
  );

  // Update column visibility when hiddenColumns change
  useEffect(() => {
    setDataColumns(
      dataColumns.map((col) => {
        return {
          ...col,
          hidden: hiddenColumns.includes(col.accessor)
        };
      })
    );
  }, [hiddenColumns]);

  // Callback when column visibility is toggled
  function toggleColumn(columnName: string) {
    let newColumns = [...dataColumns];

    let colIdx = newColumns.findIndex((col) => col.accessor == columnName);

    if (colIdx >= 0 && colIdx < newColumns.length) {
      newColumns[colIdx].hidden = !newColumns[colIdx].hidden;
    }

    let hiddenColumnNames = newColumns
      .filter((col) => col.hidden)
      .map((col) => col.accessor);

    // Save list of hidden columns to local storage
    saveHiddenColumns(tableKey, hiddenColumnNames);

    // Refresh state
    setHiddenColumns(loadHiddenColumns(tableKey));
  }

  // Check if custom filtering is enabled for this table
  const hasCustomFilters = enableFilters && customFilters.length > 0;

  // Filter selection open state
  const [filterSelectOpen, setFilterSelectOpen] = useState<boolean>(false);

  // Pagination
  const [page, setPage] = useState(1);

  // Filter list visibility
  const [filtersVisible, setFiltersVisible] = useState<boolean>(false);

  // Map of currently active filters, {name: value}
  const [activeFilters, setActiveFilters] = useState(() =>
    loadActiveFilters(tableKey, customFilters)
  );

  /*
   * Callback for the "add filter" button.
   * Launches a modal dialog to add a new filter
   */
  function onFilterAdd(name: string, value: string) {
    let filters = [...activeFilters];

    let newFilter = customFilters.find((flt) => flt.name == name);

    if (newFilter) {
      filters.push({
        ...newFilter,
        value: value
      });

      saveActiveFilters(tableKey, filters);
      setActiveFilters(filters);
    }
  }

  /*
   * Callback function when a specified filter is removed from the table
   */
  function onFilterRemove(filterName: string) {
    let filters = activeFilters.filter((flt) => flt.name != filterName);
    saveActiveFilters(tableKey, filters);
    setActiveFilters(filters);
  }

  /*
   * Callback function when all custom filters are removed from the table
   */
  function onFilterClearAll() {
    saveActiveFilters(tableKey, []);
    setActiveFilters([]);
  }

  // Search term
  const [searchTerm, setSearchTerm] = useState<string>('');

  /*
   * Construct query filters for the current table
   */
  function getTableFilters(paginate: boolean = false) {
    let queryParams = { ...params };

    // Add custom filters
    activeFilters.forEach((flt) => (queryParams[flt.name] = flt.value));

    // Add custom search term
    if (searchTerm) {
      queryParams.search = searchTerm;
    }

    // Pagination
    if (enablePagination && paginate) {
      queryParams.limit = pageSize;
      queryParams.offset = (page - 1) * pageSize;
    }

    // Ordering
    let ordering = getOrderingTerm();

    if (ordering) {
      if (sortStatus.direction == 'asc') {
        queryParams.ordering = ordering;
      } else {
        queryParams.ordering = `-${ordering}`;
      }
    }

    return queryParams;
  }

  // Data download callback
  function downloadData(fileFormat: string) {
    // Download entire dataset (no pagination)
    let queryParams = getTableFilters(false);

    // Specify file format
    queryParams.export = fileFormat;

    let downloadUrl = api.getUri({
      url: url,
      params: queryParams
    });

    // Download file in a new window (to force download)
    window.open(downloadUrl, '_blank');
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

  // Function to perform API query to fetch required data
  const fetchTableData = async () => {
    let queryParams = getTableFilters(true);

    return api
      .get(`${url}`, {
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
      page,
      activeFilters,
      searchTerm
    ],
    fetchTableData,
    {
      refetchOnWindowFocus: false,
      refetchOnMount: 'always'
    }
  );

  return (
    <>
      <FilterSelectModal
        availableFilters={customFilters}
        activeFilters={activeFilters}
        opened={filterSelectOpen}
        onCreateFilter={onFilterAdd}
        onClose={() => setFilterSelectOpen(false)}
      />
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
            {enableDownload && (
              <DownloadAction downloadCallback={downloadData} />
            )}
          </Group>
          <Space />
          <Group position="right" spacing={5}>
            {enableSearch && (
              <TableSearchInput
                searchCallback={(term: string) => setSearchTerm(term)}
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
                  <Tooltip label={t`Table filters`}>
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
            activeFilters={activeFilters}
            onFilterAdd={() => setFilterSelectOpen(true)}
            onFilterRemove={onFilterRemove}
            onFilterClearAll={onFilterClearAll}
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
    </>
  );
}
