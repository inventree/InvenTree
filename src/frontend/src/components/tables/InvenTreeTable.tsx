import { t } from '@lingui/macro';
import { ActionIcon, Indicator, Space, Stack, Tooltip } from '@mantine/core';
import { Group } from '@mantine/core';
import { useLocalStorage } from '@mantine/hooks';
import { IconFilter, IconRefresh } from '@tabler/icons-react';
import { IconBarcode, IconPrinter } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { DataTable, DataTableSortStatus } from 'mantine-datatable';
import { useEffect, useMemo, useState } from 'react';

import { api } from '../../App';
import { ButtonMenu } from '../items/ButtonMenu';
import { TableColumn } from './Column';
import { TableColumnSelect } from './ColumnSelect';
import { DownloadAction } from './DownloadAction';
import { TableFilter } from './Filter';
import { FilterGroup } from './FilterGroup';
import { FilterSelectModal } from './FilterSelectModal';
import { RowAction, RowActions } from './RowActions';
import { TableSearchInput } from './Search';

const defaultPageSize: number = 25;

/**
 * Set of optional properties which can be passed to an InvenTreeTable component
 *
 * @param url : string - The API endpoint to query
 * @param params : any - Base query parameters
 * @param tableKey : string - Unique key for the table (used for local storage)
 * @param refreshId : string - Unique ID for the table (used to trigger a refresh)
 * @param defaultSortColumn : string - Default column to sort by
 * @param noRecordsText : string - Text to display when no records are found
 * @param enableDownload : boolean - Enable download actions
 * @param enableFilters : boolean - Enable filter actions
 * @param enableSelection : boolean - Enable row selection
 * @param enableSearch : boolean - Enable search actions
 * @param enablePagination : boolean - Enable pagination
 * @param enableRefresh : boolean - Enable refresh actions
 * @param pageSize : number - Number of records per page
 * @param barcodeActions : any[] - List of barcode actions
 * @param customFilters : TableFilter[] - List of custom filters
 * @param customActionGroups : any[] - List of custom action groups
 * @param printingActions : any[] - List of printing actions
 * @param rowActions : (record: any) => RowAction[] - Callback function to generate row actions
 * @param onRowClick : (record: any, index: number, event: any) => void - Callback function when a row is clicked
 */
export type InvenTreeTableProps = {
  params?: any;
  defaultSortColumn?: string;
  noRecordsText?: string;
  enableDownload?: boolean;
  enableFilters?: boolean;
  enableSelection?: boolean;
  enableSearch?: boolean;
  enablePagination?: boolean;
  enableRefresh?: boolean;
  pageSize?: number;
  barcodeActions?: any[];
  customFilters?: TableFilter[];
  customActionGroups?: any[];
  printingActions?: any[];
  idAccessor?: string;
  rowActions?: (record: any) => RowAction[];
  onRowClick?: (record: any, index: number, event: any) => void;
};

/**
 * Default table properties (used if not specified)
 */
const defaultInvenTreeTableProps: InvenTreeTableProps = {
  params: {},
  noRecordsText: t`No records found`,
  enableDownload: false,
  enableFilters: true,
  enablePagination: true,
  enableRefresh: true,
  enableSearch: true,
  enableSelection: false,
  pageSize: defaultPageSize,
  defaultSortColumn: '',
  printingActions: [],
  barcodeActions: [],
  customFilters: [],
  customActionGroups: [],
  idAccessor: 'pk',
  rowActions: (record: any) => [],
  onRowClick: (record: any, index: number, event: any) => {}
};

/**
 * Table Component which extends DataTable with custom InvenTree functionality
 */
export function InvenTreeTable({
  url,
  tableKey,
  columns,
  props
}: {
  url: string;
  tableKey: string;
  columns: TableColumn[];
  props: InvenTreeTableProps;
}) {
  // Use the first part of the table key as the table name
  const tableName: string = useMemo(() => {
    return tableKey.split('-')[0];
  }, []);

  // Build table properties based on provided props (and default props)
  const tableProps: InvenTreeTableProps = useMemo(() => {
    return {
      ...defaultInvenTreeTableProps,
      ...props
    };
  }, [props]);

  // Check if any columns are switchable (can be hidden)
  const hasSwitchableColumns = columns.some(
    (col: TableColumn) => col.switchable
  );

  // A list of hidden columns, saved to local storage
  const [hiddenColumns, setHiddenColumns] = useLocalStorage<string[]>({
    key: `inventree-hidden-table-columns-${tableName}`,
    defaultValue: []
  });

  // Active filters (saved to local storage)
  const [activeFilters, setActiveFilters] = useLocalStorage<any[]>({
    key: `inventree-active-table-filters-${tableName}`,
    defaultValue: []
  });

  // Data selection
  const [selectedRecords, setSelectedRecords] = useState<any[]>([]);

  function onSelectedRecordsChange(records: any[]) {
    setSelectedRecords(records);
  }

  // Update column visibility when hiddenColumns change
  const dataColumns: any = useMemo(() => {
    let cols = columns.map((col) => {
      let hidden: boolean = col.hidden ?? false;

      if (col.switchable) {
        hidden = hiddenColumns.includes(col.accessor);
      }

      return {
        ...col,
        hidden: hidden
      };
    });

    // If row actions are available, add a column for them
    if (tableProps.rowActions) {
      cols.push({
        accessor: 'actions',
        title: '',
        hidden: false,
        switchable: false,
        width: 48,
        render: function (record: any) {
          return (
            <RowActions
              actions={tableProps.rowActions?.(record) ?? []}
              disabled={selectedRecords.length > 0}
            />
          );
        }
      });
    }

    return cols;
  }, [
    columns,
    hiddenColumns,
    tableProps.rowActions,
    tableProps.enableSelection,
    selectedRecords
  ]);

  // Callback when column visibility is toggled
  function toggleColumn(columnName: string) {
    let newColumns = [...dataColumns];

    let colIdx = newColumns.findIndex((col) => col.accessor == columnName);

    if (colIdx >= 0 && colIdx < newColumns.length) {
      newColumns[colIdx].hidden = !newColumns[colIdx].hidden;
    }

    setHiddenColumns(
      newColumns.filter((col) => col.hidden).map((col) => col.accessor)
    );
  }

  // Filter selection open state
  const [filterSelectOpen, setFilterSelectOpen] = useState<boolean>(false);

  // Pagination
  const [page, setPage] = useState(1);

  // Filter list visibility
  const [filtersVisible, setFiltersVisible] = useState<boolean>(false);

  /*
   * Callback for the "add filter" button.
   * Launches a modal dialog to add a new filter
   */
  function onFilterAdd(name: string, value: string) {
    let filters = [...activeFilters];

    let newFilter = tableProps.customFilters?.find((flt) => flt.name == name);

    if (newFilter) {
      filters.push({
        ...newFilter,
        value: value
      });

      setActiveFilters(filters);
    }
  }

  /*
   * Callback function when a specified filter is removed from the table
   */
  function onFilterRemove(filterName: string) {
    let filters = activeFilters.filter((flt) => flt.name != filterName);

    setActiveFilters(filters);
  }

  /*
   * Callback function when all custom filters are removed from the table
   */
  function onFilterClearAll() {
    setActiveFilters([]);
  }

  // Search term
  const [searchTerm, setSearchTerm] = useState<string>('');

  // Reset the pagination state when the search term changes
  useEffect(() => {
    setPage(1);
  }, [searchTerm]);

  /*
   * Construct query filters for the current table
   */
  function getTableFilters(paginate: boolean = false) {
    let queryParams = {
      ...tableProps.params
    };

    // Add custom filters
    activeFilters.forEach((flt) => (queryParams[flt.name] = flt.value));

    // Add custom search term
    if (searchTerm) {
      queryParams.search = searchTerm;
    }

    // Pagination
    if (tableProps.enablePagination && paginate) {
      let pageSize = tableProps.pageSize ?? defaultPageSize;
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
    columnAccessor: tableProps.defaultSortColumn ?? '',
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
    let column = dataColumns.find((col: any) => col.accessor == key);
    return column?.ordering || key;
  }

  // Missing records text (based on server response)
  const [missingRecordsText, setMissingRecordsText] = useState<string>(
    tableProps.noRecordsText ?? t`No records found`
  );

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
            setMissingRecordsText(
              tableProps.noRecordsText ?? t`No records found`
            );
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
      `table-${tableName}`,
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

  /*
   * Reload the table whenever the refetch changes
   * this allows us to programmatically refresh the table
   *
   * Implement this using the custom useTableRefresh hook
   */
  useEffect(() => {
    refetch();
  }, [tableKey, props.params]);

  return (
    <>
      <FilterSelectModal
        availableFilters={tableProps.customFilters ?? []}
        activeFilters={activeFilters}
        opened={filterSelectOpen}
        onCreateFilter={onFilterAdd}
        onClose={() => setFilterSelectOpen(false)}
      />
      <Stack>
        <Group position="apart">
          <Group position="left" spacing={5}>
            {tableProps.customActionGroups?.map(
              (group: any, idx: number) => group
            )}
            {(tableProps.barcodeActions?.length ?? 0 > 0) && (
              <ButtonMenu
                icon={<IconBarcode />}
                label={t`Barcode actions`}
                tooltip={t`Barcode actions`}
                actions={tableProps.barcodeActions ?? []}
              />
            )}
            {(tableProps.printingActions?.length ?? 0 > 0) && (
              <ButtonMenu
                icon={<IconPrinter />}
                label={t`Print actions`}
                tooltip={t`Print actions`}
                actions={tableProps.printingActions ?? []}
              />
            )}
            {tableProps.enableDownload && (
              <DownloadAction downloadCallback={downloadData} />
            )}
          </Group>
          <Space />
          <Group position="right" spacing={5}>
            {tableProps.enableSearch && (
              <TableSearchInput
                searchCallback={(term: string) => setSearchTerm(term)}
              />
            )}
            {tableProps.enableRefresh && (
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
            {tableProps.enableFilters &&
              (tableProps.customFilters?.length ?? 0 > 0) && (
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
          idAccessor={tableProps.idAccessor}
          minHeight={200}
          totalRecords={data?.count ?? data?.length ?? 0}
          recordsPerPage={tableProps.pageSize ?? defaultPageSize}
          page={page}
          onPageChange={setPage}
          sortStatus={sortStatus}
          onSortStatusChange={handleSortStatusChange}
          selectedRecords={
            tableProps.enableSelection ? selectedRecords : undefined
          }
          onSelectedRecordsChange={
            tableProps.enableSelection ? onSelectedRecordsChange : undefined
          }
          fetching={isFetching}
          noRecordsText={missingRecordsText}
          records={data?.results ?? data ?? []}
          columns={dataColumns}
          onRowClick={tableProps.onRowClick}
        />
      </Stack>
    </>
  );
}
