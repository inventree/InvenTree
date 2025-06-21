import { t } from '@lingui/core/macro';
import { Box, type MantineStyleProp, Stack } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import {
  type ContextMenuItemOptions,
  useContextMenu
} from 'mantine-contextmenu';
import {
  DataTable,
  type DataTableCellClickHandler,
  type DataTableRowExpansionProps,
  type DataTableSortStatus,
  useDataTableColumns
} from 'mantine-datatable';
import type React from 'react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import type { ModelType } from '@lib/enums/ModelType';
import { cancelEvent } from '@lib/functions/Events';
import { getDetailUrl } from '@lib/functions/Navigation';
import { navigateToLink } from '@lib/functions/Navigation';
import type { TableFilter } from '@lib/types/Filters';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import type { TableState } from '@lib/types/Tables';
import { hideNotification, showNotification } from '@mantine/notifications';
import { IconArrowRight } from '@tabler/icons-react';
import { Boundary } from '../components/Boundary';
import { useApi } from '../contexts/ApiContext';
import { resolveItem } from '../functions/conversion';
import { extractAvailableFields, mapFields } from '../functions/forms';
import { useLocalState } from '../states/LocalState';
import type { TableColumn } from './Column';
import InvenTreeTableHeader from './InvenTreeTableHeader';
import { type RowAction, RowActions } from './RowActions';

const ACTIONS_COLUMN_ACCESSOR: string = '--actions--';
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
 * @param hideActionsColumn : boolean - Hide the actions column (default false)
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
  hideActionsColumn?: boolean;
  onRowClick?: (record: T, index: number, event: any) => void;
  onCellClick?: DataTableCellClickHandler<T>;
  modelType?: ModelType;
  rowStyle?: (record: T, index: number) => MantineStyleProp | undefined;
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
    userTheme
  } = useLocalState();

  const [fieldNames, setFieldNames] = useState<Record<string, string>>({});

  const api = useApi();
  const navigate = useNavigate();
  const { showContextMenu } = useContextMenu();

  // Key used for caching table data
  const cacheKey = useMemo(() => {
    const key: string = `table-${tableState.tableKey}`;

    // Remove anything after (and including) "mantine"
    const mantineIndex = key.indexOf('-mantine');
    if (mantineIndex >= 0) {
      return key.substring(0, mantineIndex);
    } else {
      return key;
    }
  }, [tableState.tableKey]);

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

  // Build table properties based on provided props (and default props)
  const tableProps: InvenTreeTableProps<T> = useMemo(() => {
    return {
      ...defaultInvenTreeTableProps,
      ...props
    };
  }, [props]);

  // Request OPTIONS data from the API, before we load the table
  const tableOptionQuery = useQuery({
    enabled: !!url && !tableData,
    queryKey: [
      'options',
      url,
      cacheKey,
      tableProps.params,
      props.enableColumnCaching
    ],
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

    // First check the local cache
    const cachedNames = getTableColumnNames(cacheKey);

    if (cachedNames != null) {
      // Cached names are available - use them!
      setFieldNames(cachedNames);
      return;
    }

    tableOptionQuery.refetch();
  }, [cacheKey, url, props.params, props.enableColumnCaching]);

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
          resizable: col.resizable ?? true,
          title: col.title ?? fieldNames[col.accessor] ?? `${col.accessor}`
        };
      });

    // If row actions are available, add a column for them
    if (tableProps.rowActions && !tableProps.hideActionsColumn) {
      cols.push({
        accessor: ACTIONS_COLUMN_ACCESSOR,
        title: '   ',
        hidden: false,
        resizable: false,
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

  // Final state of the table columns
  const tableColumns = useDataTableColumns({
    key: cacheKey,
    columns: dataColumns
  });

  // Ensure that the "actions" column is always at the end of the list
  // This effect is necessary as sometimes the underlying mantine-datatable columns change
  useEffect(() => {
    const idx: number = tableColumns.columnsOrder.indexOf(
      ACTIONS_COLUMN_ACCESSOR
    );

    if (idx >= 0 && idx < tableColumns.columnsOrder.length - 1) {
      // Actions column is not at the end of the list - move it there
      const newOrder = tableColumns.columnsOrder.filter(
        (col) => col != ACTIONS_COLUMN_ACCESSOR
      );
      newOrder.push(ACTIONS_COLUMN_ACCESSOR);
      tableColumns.setColumnsOrder(newOrder);
    }
  }, [tableColumns.columnsOrder]);

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
      if (tableState.filterSet.activeFilters) {
        tableState.filterSet.activeFilters.forEach((flt) => {
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
      tableState.filterSet.activeFilters,
      tableState.queryFilters,
      tableState.searchTerm,
      tableState.pageSize,
      tableState.setPageSize,
      sortStatus,
      getOrderingTerm
    ]
  );

  const [sortingLoaded, setSortingLoaded] = useState<boolean>(false);

  useEffect(() => {
    const tableKey: string = tableState.tableKey.split('-')[0];
    const sorting: DataTableSortStatus = getTableSorting(tableKey);

    if (sorting && !!sorting.columnAccessor && !!sorting.direction) {
      setSortStatus(sorting);
    }

    setSortingLoaded(true);
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
      // No URL supplied - do not load!
      return [];
    }

    if (!sortingLoaded) {
      // Sorting not yet loaded - do not load!
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
      sortingLoaded,
      sortStatus.columnAccessor,
      sortStatus.direction,
      tableState.tableKey,
      tableState.filterSet.activeFilters,
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
    const loading: boolean =
      isFetching ||
      isLoading ||
      tableOptionQuery.isFetching ||
      tableOptionQuery.isLoading;

    if (loading != tableState.isLoading) {
      tableState.setIsLoading(loading);
    }
  }, [
    isFetching,
    isLoading,
    tableOptionQuery.isFetching,
    tableOptionQuery.isLoading,
    tableState.isLoading
  ]);

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
      if (column.accessor == ACTIONS_COLUMN_ACCESSOR) {
        return;
      }

      if (props.onCellClick) {
        props.onCellClick({ event, record, index, column, columnIndex });
      } else if (props.onRowClick) {
        props.onRowClick(record, index, event);
      } else if (!!tableProps.rowExpansion) {
        // No action here, handled by row expansion
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

  const supportsContextMenu = useMemo(() => {
    return !!props.onCellContextMenu || !!props.rowActions || !!props.modelType;
  }, [props.onCellContextMenu, props.rowActions, props.modelType]);

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
    }

    const empty = () => {};
    let items: ContextMenuItemOptions[] = [];

    if (props.rowActions) {
      items = props.rowActions(record).map((action) => ({
        key: action.title ?? '',
        title: action.title ?? '',
        color: action.color,
        icon: action.icon,
        onClick: action.onClick ?? empty,
        hidden: action.hidden,
        disabled: action.disabled
      }));
    }

    if (props.modelType) {
      // Add action to navigate to the detail view
      const accessor = props.modelField ?? 'pk';
      const pk = resolveItem(record, accessor);
      const url = getDetailUrl(props.modelType, pk);
      items.push({
        key: 'detail',
        title: t`View details`,
        icon: <IconArrowRight />,
        onClick: (event: any) => {
          cancelEvent(event);
          navigateToLink(url, navigate, event);
        }
      });
    }

    return showContextMenu(items)(event);
  };

  // pagination refresh table if pageSize changes
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

  const supportsCellClick = useMemo(() => {
    return !!(
      tableProps.onCellClick ||
      tableProps.onRowClick ||
      tableProps.modelType
    );
  }, [tableProps.onCellClick, tableProps.onRowClick, tableProps.modelType]);

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
              loaderType={userTheme.loader}
              pinLastColumn={
                !tableProps.hideActionsColumn &&
                tableProps.rowActions != undefined
              }
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
              fetching={isFetching}
              noRecordsText={missingRecordsText}
              records={tableState.records}
              storeColumnsKey={cacheKey}
              columns={tableColumns.effectiveColumns}
              onCellClick={supportsCellClick ? handleCellClick : undefined}
              noHeader={tableProps.noHeader ?? false}
              defaultColumnProps={{
                textAlign: 'left'
              }}
              onCellContextMenu={
                supportsContextMenu ? handleCellContextMenu : undefined
              }
              {...optionalParams}
            />
          </Box>
        </Boundary>
      </Stack>
    </>
  );
}
