import { t } from '@lingui/macro';
import { Box, Stack } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { useContextMenu } from 'mantine-contextmenu';
import {
  DataTable,
  type DataTableCellClickHandler,
  type DataTableRowExpansionProps,
  type DataTableSortStatus
} from 'mantine-datatable';
import type React from 'react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { hideNotification, showNotification } from '@mantine/notifications';
import { Boundary } from '../components/Boundary';
import type { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';
import { useApi } from '../contexts/ApiContext';
import type { ModelType } from '../enums/ModelType';
import { resolveItem } from '../functions/conversion';
import { cancelEvent } from '../functions/events';
import { extractAvailableFields, mapFields } from '../functions/forms';
import { navigateToLink } from '../functions/navigation';
import { getDetailUrl } from '../functions/urls';
import type { TableState } from '../hooks/UseTable';
import { useLocalState } from '../states/LocalState';
import type { TableColumn } from './Column';
import type { TableFilter } from './Filter';
import InvenTreeTableHeader from './InvenTreeTableHeader';
import { type RowAction, RowActions } from './RowActions';

const defaultPageSize: number = 25;
const PAGE_SIZES = [10, 15, 20, 25, 50, 100, 500];

/**
 * Set of optional properties which can be passed to an InvenTreeTable component
 *
 * @param params : any - Base query parameters
 * @param tableState : TableState - State manager for the table
 * @param defaultSortColumn : string - Default column to sort by
 * @param noRecordsText : string - Text to display when no records are found
 * @param enableBulkDelete : boolean - Enable bulk deletion of records
 * @param enableDownload : boolean - Enable download actions
 * @param enableFilters : boolean - Enable filter actions
 * @param enableSelection : boolean - Enable row selection
 * @param enableSearch : boolean - Enable search actions
 * @param enableLabels : boolean - Enable printing of labels against selected items
 * @param enableReports : boolean - Enable printing of reports against selected items
 * @param enablePagination : boolean - Enable pagination
 * @param enableRefresh : boolean - Enable refresh actions
 * @param enableColumnSwitching : boolean - Enable column switching
 * @param enableColumnCaching : boolean - Enable caching of column names via API
 * @param barcodeActions : any[] - List of barcode actions
 * @param tableFilters : TableFilter[] - List of custom filters
 * @param tableActions : any[] - List of custom action groups
 * @param dataFormatter : (data: any) => any - Callback function to reformat data returned by server (if not in default format)
 * @param rowActions : (record: any) => RowAction[] - Callback function to generate row actions
 * @param onRowClick : (record: any, index: number, event: any) => void - Callback function when a row is clicked
 * @param onCellClick : (event: any, record: any, index: number, column: any, columnIndex: number) => void - Callback function when a cell is clicked
 * @param modelType: ModelType - The model type for the table
 * @param minHeight: number - Minimum height of the table (default 300px)
 * @param noHeader: boolean - Hide the table header
 */
export type InvenTreeTableProps<T = any> = {
  params?: any;
  defaultSortColumn?: string;
  noRecordsText?: string;
  enableBulkDelete?: boolean;
  enableDownload?: boolean;
  enableFilters?: boolean;
  enableSelection?: boolean;
  enableSearch?: boolean;
  enablePagination?: boolean;
  enableRefresh?: boolean;
  enableColumnSwitching?: boolean;
  enableColumnCaching?: boolean;
  enableLabels?: boolean;
  enableReports?: boolean;
  afterBulkDelete?: () => void;
  barcodeActions?: React.ReactNode[];
  tableFilters?: TableFilter[];
  tableActions?: React.ReactNode[];
  rowExpansion?: DataTableRowExpansionProps<T>;
  dataFormatter?: (data: any) => any;
  rowActions?: (record: T) => RowAction[];
  onRowClick?: (record: T, index: number, event: any) => void;
  onCellClick?: DataTableCellClickHandler<T>;
  modelType?: ModelType;
  rowStyle?: (record: T, index: number) => any;
  modelField?: string;
  onCellContextMenu?: (record: T, event: any) => void;
  minHeight?: number;
  noHeader?: boolean;
};

/**
 * Default table properties (used if not specified)
 */
const defaultInvenTreeTableProps: InvenTreeTableProps = {
  params: {},
  noRecordsText: t`No records found`,
  enableDownload: false,
  enableLabels: false,
  enableReports: false,
  enableFilters: true,
  enablePagination: true,
  enableRefresh: true,
  enableSearch: true,
  enableSelection: false,
  defaultSortColumn: '',
  barcodeActions: [],
  tableFilters: [],
  tableActions: []
};

/**
 * Table Component which extends DataTable with custom InvenTree functionality
 */
export function InvenTreeTable<T extends Record<string, any>>({
  url,
  tableState,
  tableData,
  columns,
  props
}: Readonly<{
  url?: string;
  tableState: TableState;
  tableData?: any[];
  columns: TableColumn<T>[];
  props: InvenTreeTableProps<T>;
}>) {
  const {
    getTableColumnNames,
    setTableColumnNames,
    getTableSorting,
    setTableSorting,
    loader
  } = useLocalState();

  const [fieldNames, setFieldNames] = useState<Record<string, string>>({});

  const api = useApi();
  const navigate = useNavigate();
  const { showContextMenu } = useContextMenu();

  // Construct table filters - note that we can introspect filter labels from column names
  const filters: TableFilter[] = useMemo(() => {
    return (
      props.tableFilters
        ?.filter((f: any) => f.active != false)
        ?.map((filter) => {
          return {
            ...filter,
            label: filter.label ?? fieldNames[filter.name] ?? `${filter.name}`
          };
        }) ?? []
    );
  }, [props.tableFilters, fieldNames]);

  // Request OPTIONS data from the API, before we load the table
  const tableOptionQuery = useQuery({
    enabled: !!url && !tableData,
    queryKey: ['options', url, tableState.tableKey, props.enableColumnCaching],
    retry: 3,
    refetchOnMount: true,
    gcTime: 5000,
    queryFn: async () => {
      if (!url) {
        return null;
      }

      if (props.enableColumnCaching == false) {
        return null;
      }

      // If we already have field names, no need to fetch them again
      if (fieldNames && Object.keys(fieldNames).length > 0) {
        return null;
      }

      return api
        .options(url, {
          params: tableProps.params
        })
        .then((response) => {
          if (response.status == 200) {
            // Extract field information from the API

            const names: Record<string, string> = {};

            const fields: ApiFormFieldSet =
              extractAvailableFields(response, 'GET', true) || {};

            // Extract flattened map of fields
            mapFields(fields, (path, field) => {
              if (field.label) {
                names[path] = field.label;
              }
            });

            const cacheKey = tableState.tableKey.replaceAll('-', '');

            setFieldNames(names);
            setTableColumnNames(cacheKey)(names);
          }

          return null;
        })
        .catch(() => {
          hideNotification('table-options-error');
          showNotification({
            id: 'table-options-error',
            title: t`API Error`,
            message: t`Failed to load table options`,
            color: 'red'
          });

          return null;
        });
    }
  });

  // Rebuild set of translated column names
  useEffect(() => {
    if (props.enableColumnCaching == false) {
      return;
    }

    const cacheKey = tableState.tableKey.replaceAll('-', '');

    // First check the local cache
    const cachedNames = getTableColumnNames(cacheKey);

    if (cachedNames != null) {
      // Cached names are available - use them!
      setFieldNames(cachedNames);
      return;
    }

    tableOptionQuery.refetch();
  }, [url, props.params, props.enableColumnCaching]);

  // Build table properties based on provided props (and default props)
  const tableProps: InvenTreeTableProps<T> = useMemo(() => {
    return {
      ...defaultInvenTreeTableProps,
      ...props
    };
  }, [props]);

  const enableSelection: boolean = useMemo(() => {
    return tableProps.enableSelection || tableProps.enableBulkDelete || false;
  }, [tableProps]);

  // Check if any columns are switchable (can be hidden)
  const hasSwitchableColumns: boolean = useMemo(() => {
    if (props.enableColumnSwitching == false) {
      return false;
    } else {
      return columns.some((col: TableColumn) => {
        if (col.hidden == true) {
          // Not a switchable column - is hidden
          return false;
        } else if (col.switchable == false) {
          return false;
        } else {
          return true;
        }
      });
    }
  }, [columns, props.enableColumnSwitching]);

  const onSelectedRecordsChange = useCallback(
    (records: any[]) => {
      tableState.setSelectedRecords(records);
    },
    [tableState.setSelectedRecords]
  );

  // Update column visibility when hiddenColumns change
  const dataColumns: any = useMemo(() => {
    const cols: TableColumn[] = columns
      .filter((col) => col?.hidden != true)
      .map((col) => {
        let hidden: boolean = col.hidden ?? false;

        if (col.switchable ?? true) {
          hidden = tableState.hiddenColumns.includes(col.accessor);
        }

        return {
          ...col,
          hidden: hidden,
          noWrap: true,
          title: col.title ?? fieldNames[col.accessor] ?? `${col.accessor}`
        };
      });

    // If row actions are available, add a column for them
    if (tableProps.rowActions) {
      cols.push({
        accessor: '--actions--',
        title: '   ',
        hidden: false,
        switchable: false,
        width: 50,
        render: (record: any, index?: number | undefined) => (
          <RowActions
            actions={tableProps.rowActions?.(record) ?? []}
            disabled={tableState.selectedRecords.length > 0}
            index={index}
          />
        )
      });
    }

    return cols;
  }, [
    columns,
    fieldNames,
    tableProps.rowActions,
    tableState.hiddenColumns,
    tableState.selectedRecords
  ]);

  // Callback when column visibility is toggled
  function toggleColumn(columnName: string) {
    const newColumns = [...dataColumns];

    const colIdx = newColumns.findIndex((col) => col.accessor == columnName);

    if (colIdx >= 0 && colIdx < newColumns.length) {
      newColumns[colIdx].hidden = !newColumns[colIdx].hidden;
    }

    tableState.setHiddenColumns(
      newColumns.filter((col) => col.hidden).map((col) => col.accessor)
    );
  }

  // Reset the pagination state when the search term changes
  useEffect(() => {
    tableState.setPage(1);
  }, [tableState.searchTerm]);

  // Data Sorting
  const [sortStatus, setSortStatus] = useState<DataTableSortStatus<T>>({
    columnAccessor: tableProps.defaultSortColumn ?? '',
    direction: 'asc'
  });

  /*
   * Construct query filters for the current table
   */
  const getTableFilters = useCallback(
    (paginate = false) => {
      const queryParams = {
        ...tableProps.params
      };

      // Add custom filters
      if (tableState.activeFilters) {
        tableState.activeFilters.forEach((flt) => {
          queryParams[flt.name] = flt.value;
        });
      }

      // Allow override of filters based on URL query parameters
      if (tableState.queryFilters) {
        for (const [key, value] of tableState.queryFilters) {
          queryParams[key] = value;
        }
      }

      // Add custom search term
      if (tableState.searchTerm) {
        queryParams.search = tableState.searchTerm;
      }

      // Pagination
      if (tableProps.enablePagination && paginate) {
        const pageSize = tableState.pageSize ?? defaultPageSize;
        if (pageSize != tableState.pageSize) tableState.setPageSize(pageSize);
        queryParams.limit = pageSize;
        queryParams.offset = (tableState.page - 1) * pageSize;
      }

      // Ordering
      const ordering = getOrderingTerm();

      if (ordering) {
        if (sortStatus.direction == 'asc') {
          queryParams.ordering = ordering;
        } else {
          queryParams.ordering = `-${ordering}`;
        }
      }

      return queryParams;
    },
    [
      tableProps.params,
      tableProps.enablePagination,
      tableState.activeFilters,
      tableState.queryFilters,
      tableState.searchTerm,
      tableState.pageSize,
      tableState.setPageSize,
      sortStatus,
      getOrderingTerm
    ]
  );

  useEffect(() => {
    const tableKey: string = tableState.tableKey.split('-')[0];
    const sorting: DataTableSortStatus = getTableSorting(tableKey);

    if (sorting) {
      setSortStatus(sorting);
    }
  }, []);

  // Return the ordering parameter
  function getOrderingTerm() {
    const key = sortStatus.columnAccessor;

    // Sorting column not specified
    if (key == '') {
      return '';
    }

    // Find matching column:
    // If column provides custom ordering term, use that
    const column = dataColumns.find((col: any) => col.accessor == key);
    return column?.ordering || key;
  }

  // Missing records text (based on server response)
  const [missingRecordsText, setMissingRecordsText] = useState<string>(
    tableProps.noRecordsText ?? t`No records found`
  );

  const handleSortStatusChange = (status: DataTableSortStatus<T>) => {
    tableState.setPage(1);
    setSortStatus(status);

    const tableKey = tableState.tableKey.split('-')[0];
    setTableSorting(tableKey)(status);
  };

  // Function to perform API query to fetch required data
  const fetchTableData = async () => {
    const queryParams = getTableFilters(true);

    if (!url) {
      return [];
    }

    return api
      .get(url, {
        params: queryParams,
        timeout: 5 * 1000
      })
      .then((response) => {
        switch (response.status) {
          case 200:
            setMissingRecordsText(
              tableProps.noRecordsText ?? t`No records found`
            );

            let results = response.data?.results ?? response.data ?? [];

            if (props.dataFormatter) {
              // Custom data formatter provided
              results = props.dataFormatter(results);
            }

            if (!Array.isArray(results)) {
              setMissingRecordsText(t`Server returned incorrect data type`);
              results = [];
            }

            tableState.setRecordCount(response.data?.count ?? results.length);

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
              `${t`Unknown error`}: ${response.statusText}`
            );
            break;
        }

        return [];
      })
      .catch((error) => {
        setMissingRecordsText(`${t`Error`}: ${error.message}`);
        return [];
      });
  };

  const {
    data: apiData,
    isFetching,
    isLoading,
    refetch
  } = useQuery({
    queryKey: [
      'tabledata',
      url,
      tableState.page,
      props.params,
      sortStatus.columnAccessor,
      sortStatus.direction,
      tableState.tableKey,
      tableState.activeFilters,
      tableState.searchTerm
    ],
    enabled: !!url && !tableData,
    queryFn: fetchTableData,
    refetchOnMount: true
  });

  // Refetch data when the query parameters change
  useEffect(() => {
    refetch();
  }, [tableState.queryFilters]);

  useEffect(() => {
    tableState.setIsLoading(
      isFetching ||
        isLoading ||
        tableOptionQuery.isFetching ||
        tableOptionQuery.isLoading
    );
  }, [isFetching, isLoading, tableOptionQuery]);

  // Update tableState.records when new data received
  useEffect(() => {
    const data = tableData ?? apiData ?? [];

    tableState.setRecords(data);

    // set pagesize to length if pagination is disabled
    if (!tableProps.enablePagination) {
      tableState.setPageSize(data?.length ?? defaultPageSize);
    }
  }, [tableData, apiData]);

  // Callback when a cell is clicked
  const handleCellClick = useCallback(
    ({
      event,
      record,
      index,
      column,
      columnIndex
    }: {
      event: React.MouseEvent;
      record: any;
      index: number;
      column: any;
      columnIndex: number;
    }) => {
      // Ignore any click on the 'actions' column
      if (column.accessor == '--actions--') {
        return;
      }

      if (props.onCellClick) {
        props.onCellClick({ event, record, index, column, columnIndex });
      } else if (props.onRowClick) {
        props.onRowClick(record, index, event);
      } else if (tableProps.modelType) {
        const accessor = tableProps.modelField ?? 'pk';
        const pk = resolveItem(record, accessor);

        if (pk) {
          cancelEvent(event);
          // If a model type is provided, navigate to the detail view for that model
          const url = getDetailUrl(tableProps.modelType, pk);
          navigateToLink(url, navigate, event);
        }
      }
    },
    [props.onRowClick, props.onCellClick]
  );

  // Callback when a cell is right-clicked
  const handleCellContextMenu = ({
    record,
    column,
    event
  }: {
    record: any;
    column: any;
    event: any;
  }) => {
    if (column?.noContext === true) {
      return;
    }
    if (props.onCellContextMenu) {
      return props.onCellContextMenu(record, event);
    } else if (props.rowActions) {
      const empty = () => {};
      const items = props.rowActions(record).map((action) => ({
        key: action.title ?? '',
        title: action.title ?? '',
        color: action.color,
        icon: action.icon,
        onClick: action.onClick ?? empty,
        hidden: action.hidden,
        disabled: action.disabled
      }));
      return showContextMenu(items)(event);
    } else {
      return showContextMenu([])(event);
    }
  };

  // pagination refresth table if pageSize changes
  function updatePageSize(newData: number) {
    tableState.setPageSize(newData);
    tableState.setPage(1);
    tableState.refreshTable();
  }

  /**
   * Memoize row expansion options:
   * - If rowExpansion is not provided, return undefined
   * - Otherwise, return the rowExpansion object
   * - Utilize the useTable hook to track expanded rows
   */
  const rowExpansion: DataTableRowExpansionProps<T> | undefined =
    useMemo(() => {
      if (!props.rowExpansion) {
        return undefined;
      }

      return {
        ...props.rowExpansion,
        expanded: {
          recordIds: tableState.expandedRecords,
          onRecordIdsChange: (ids: any[]) => {
            tableState.setExpandedRecords(ids);
          }
        }
      };
    }, [
      tableState.expandedRecords,
      tableState.setExpandedRecords,
      props.rowExpansion
    ]);

  const optionalParams = useMemo(() => {
    let _params: Record<string, any> = {};

    if (tableProps.enablePagination) {
      _params = {
        ..._params,
        totalRecords: tableState.recordCount,
        recordsPerPage: tableState.pageSize,
        page: tableState.page,
        onPageChange: tableState.setPage,
        recordsPerPageOptions: PAGE_SIZES,
        onRecordsPerPageChange: updatePageSize
      };
    }

    return _params;
  }, [
    tableProps.enablePagination,
    tableState.recordCount,
    tableState.pageSize,
    tableState.page,
    tableState.setPage,
    updatePageSize
  ]);

  return (
    <>
      <Stack gap='xs'>
        {!tableProps.noHeader && (
          <Boundary label={`InvenTreeTableHeader-${tableState.tableKey}`}>
            <InvenTreeTableHeader
              tableUrl={url}
              tableState={tableState}
              tableProps={tableProps}
              hasSwitchableColumns={hasSwitchableColumns}
              columns={dataColumns}
              filters={filters}
              toggleColumn={toggleColumn}
            />
          </Boundary>
        )}
        <Boundary label={`InvenTreeTable-${tableState.tableKey}`}>
          <Box pos='relative'>
            <DataTable
              withTableBorder={!tableProps.noHeader}
              withColumnBorders
              striped
              highlightOnHover
              loaderType={loader}
              pinLastColumn={tableProps.rowActions != undefined}
              idAccessor={tableState.idAccessor ?? 'pk'}
              minHeight={tableProps.minHeight ?? 300}
              sortStatus={sortStatus}
              onSortStatusChange={handleSortStatusChange}
              selectedRecords={
                enableSelection ? tableState.selectedRecords : undefined
              }
              onSelectedRecordsChange={
                enableSelection ? onSelectedRecordsChange : undefined
              }
              rowExpansion={rowExpansion}
              rowStyle={tableProps.rowStyle}
              fetching={isFetching}
              noRecordsText={missingRecordsText}
              records={tableState.records}
              columns={dataColumns}
              onCellClick={handleCellClick}
              noHeader={tableProps.noHeader ?? false}
              defaultColumnProps={{
                noWrap: true,
                textAlign: 'left',
                cellsStyle: () => (theme) => ({
                  // TODO @SchrodingersGat : Need a better way of handling "wide" cells,
                  overflow: 'hidden'
                })
              }}
              onCellContextMenu={handleCellContextMenu}
              {...optionalParams}
            />
          </Box>
        </Boundary>
      </Stack>
    </>
  );
}
