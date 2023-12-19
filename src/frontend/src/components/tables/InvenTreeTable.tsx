import { t } from '@lingui/macro';
import { ActionIcon, Indicator, Space, Stack, Tooltip } from '@mantine/core';
import { Group } from '@mantine/core';
import { IconFilter, IconRefresh } from '@tabler/icons-react';
import { IconBarcode, IconPrinter } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { DataTable, DataTableSortStatus } from 'mantine-datatable';
import { Fragment, useCallback, useEffect, useMemo, useState } from 'react';

import { api } from '../../App';
import { TableState } from '../../hooks/UseTable';
import { ButtonMenu } from '../buttons/ButtonMenu';
import { TableColumn } from './Column';
import { TableColumnSelect } from './ColumnSelect';
import { DownloadAction } from './DownloadAction';
import { TableFilter } from './Filter';
import { FilterSelectDrawer } from './FilterSelectDrawer';
import { RowAction, RowActions } from './RowActions';
import { TableSearchInput } from './Search';

const defaultPageSize: number = 25;

/**
 * Set of optional properties which can be passed to an InvenTreeTable component
 *
 * @param params : any - Base query parameters
 * @param tableState : TableState - State manager for the table
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
 * @param dataFormatter : (data: any) => any - Callback function to reformat data returned by server (if not in default format)
 * @param rowActions : (record: any) => RowAction[] - Callback function to generate row actions
 * @param onRowClick : (record: any, index: number, event: any) => void - Callback function when a row is clicked
 */
export type InvenTreeTableProps<T = any> = {
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
  customActionGroups?: React.ReactNode[];
  printingActions?: any[];
  idAccessor?: string;
  dataFormatter?: (data: T) => any;
  rowActions?: (record: T) => RowAction[];
  onRowClick?: (record: T, index: number, event: any) => void;
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
  onRowClick: (record: any, index: number, event: any) => {}
};

/**
 * Table Component which extends DataTable with custom InvenTree functionality
 */
export function InvenTreeTable<T = any>({
  url,
  tableState,
  columns,
  props
}: {
  url: string;
  tableState: TableState;
  columns: TableColumn<T>[];
  props: InvenTreeTableProps<T>;
}) {
  // Build table properties based on provided props (and default props)
  const tableProps: InvenTreeTableProps<T> = useMemo(() => {
    return {
      ...defaultInvenTreeTableProps,
      ...props
    };
  }, [props]);

  // Check if any columns are switchable (can be hidden)
  const hasSwitchableColumns = columns.some(
    (col: TableColumn) => col.switchable ?? true
  );

  const onSelectedRecordsChange = useCallback((records: any[]) => {
    tableState.setSelectedRecords(records);
  }, []);

  // Update column visibility when hiddenColumns change
  const dataColumns: any = useMemo(() => {
    let cols = columns.map((col) => {
      let hidden: boolean = col.hidden ?? false;

      if (col.switchable ?? true) {
        hidden = tableState.hiddenColumns.includes(col.accessor);
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
        title: '   ',
        hidden: false,
        switchable: false,
        width: 50,
        render: function (record: any) {
          return (
            <RowActions
              actions={tableProps.rowActions?.(record) ?? []}
              disabled={tableState.selectedRecords.length > 0}
            />
          );
        }
      });
    }

    return cols;
  }, [
    columns,
    tableProps.rowActions,
    tableProps.enableSelection,
    tableState.hiddenColumns,
    tableState.selectedRecords
  ]);

  // Callback when column visibility is toggled
  function toggleColumn(columnName: string) {
    let newColumns = [...dataColumns];

    let colIdx = newColumns.findIndex((col) => col.accessor == columnName);

    if (colIdx >= 0 && colIdx < newColumns.length) {
      newColumns[colIdx].hidden = !newColumns[colIdx].hidden;
    }

    tableState.setHiddenColumns(
      newColumns.filter((col) => col.hidden).map((col) => col.accessor)
    );
  }

  // Pagination
  const [page, setPage] = useState(1);

  // Filter list visibility
  const [filtersVisible, setFiltersVisible] = useState<boolean>(false);

  // Reset the pagination state when the search term changes
  useEffect(() => {
    setPage(1);
  }, [tableState.searchTerm]);

  /*
   * Construct query filters for the current table
   */
  function getTableFilters(paginate: boolean = false) {
    let queryParams = {
      ...tableProps.params
    };

    // Add custom filters
    tableState.activeFilters.forEach(
      (flt) => (queryParams[flt.name] = flt.value)
    );

    // Add custom search term
    if (tableState.searchTerm) {
      queryParams.search = tableState.searchTerm;
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

            let results = [];

            if (props.dataFormatter) {
              // Custom data formatter provided
              results = props.dataFormatter(response.data);
            } else {
              // Extract returned data (accounting for pagination) and ensure it is a list
              results = response.data?.results ?? response.data ?? [];
            }

            if (!Array.isArray(results)) {
              setMissingRecordsText(t`Server returned incorrect data type`);
              results = [];
            }

            setRecordCount(response.data?.count ?? results.length);

            return results;
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
            );
            break;
        }

        return [];
      })
      .catch(function (error) {
        setMissingRecordsText(t`Error` + ': ' + error.message);
        return [];
      });
  };

  const { data, isFetching, refetch } = useQuery({
    queryKey: [
      page,
      props.params,
      sortStatus.columnAccessor,
      sortStatus.direction,
      tableState.tableKey,
      tableState.activeFilters,
      tableState.searchTerm
    ],
    queryFn: fetchTableData,
    refetchOnWindowFocus: false,
    refetchOnMount: true
  });

  const [recordCount, setRecordCount] = useState<number>(0);

  return (
    <>
      {tableProps.enableFilters &&
        (tableProps.customFilters?.length ?? 0) > 0 && (
          <FilterSelectDrawer
            availableFilters={tableProps.customFilters ?? []}
            tableState={tableState}
            opened={filtersVisible}
            onClose={() => setFiltersVisible(false)}
          />
        )}
      <Stack spacing="sm">
        <Group position="apart">
          <Group position="left" key="custom-actions" spacing={5}>
            {tableProps.customActionGroups?.map((group, idx) => (
              <Fragment key={idx}>{group}</Fragment>
            ))}
            {(tableProps.barcodeActions?.length ?? 0 > 0) && (
              <ButtonMenu
                key="barcode-actions"
                icon={<IconBarcode />}
                label={t`Barcode actions`}
                tooltip={t`Barcode actions`}
                actions={tableProps.barcodeActions ?? []}
              />
            )}
            {(tableProps.printingActions?.length ?? 0 > 0) && (
              <ButtonMenu
                key="printing-actions"
                icon={<IconPrinter />}
                label={t`Print actions`}
                tooltip={t`Print actions`}
                actions={tableProps.printingActions ?? []}
              />
            )}
          </Group>
          <Space />
          <Group position="right" spacing={5}>
            {tableProps.enableSearch && (
              <TableSearchInput
                searchCallback={(term: string) =>
                  tableState.setSearchTerm(term)
                }
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
                  label={tableState.activeFilters.length}
                  disabled={tableState.activeFilters.length == 0}
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
            {tableProps.enableDownload && (
              <DownloadAction
                key="download-action"
                downloadCallback={downloadData}
              />
            )}
          </Group>
        </Group>
        <DataTable
          withBorder
          striped
          highlightOnHover
          loaderVariant="dots"
          pinLastColumn={tableProps.rowActions != undefined}
          idAccessor={tableProps.idAccessor}
          minHeight={300}
          totalRecords={recordCount}
          recordsPerPage={tableProps.pageSize ?? defaultPageSize}
          page={page}
          onPageChange={setPage}
          sortStatus={sortStatus}
          onSortStatusChange={handleSortStatusChange}
          selectedRecords={
            tableProps.enableSelection ? tableState.selectedRecords : undefined
          }
          onSelectedRecordsChange={
            tableProps.enableSelection ? onSelectedRecordsChange : undefined
          }
          fetching={isFetching}
          noRecordsText={missingRecordsText}
          records={data}
          columns={dataColumns}
          onRowClick={tableProps.onRowClick}
          defaultColumnProps={{
            noWrap: true,
            textAlignment: 'left',
            cellsStyle: {
              // TODO: Need a better way of handling "wide" cells,
              overflow: 'hidden'
            }
          }}
        />
      </Stack>
    </>
  );
}
