import { RowActions } from '@lib/components/RowActions';
import { ModelInformationDict } from '@lib/enums/ModelInformation';
import { resolveItem } from '@lib/functions/Conversion';
import { cancelEvent } from '@lib/functions/Events';
import { getDetailUrl } from '@lib/functions/Navigation';
import { navigateToLink } from '@lib/functions/Navigation';
import type { TableFilter } from '@lib/types/Filters';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import type { InvenTreeTableProps, TableState } from '@lib/types/Tables';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { Box, Stack } from '@mantine/core';
import { IconArrowRight } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import {
  type ContextMenuItemOptions,
  useContextMenu
} from 'mantine-contextmenu';
import {
  DataTable,
  type DataTableRowExpansionProps,
  type DataTableSortStatus,
  useDataTableColumns
} from 'mantine-datatable';
import type React from 'react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Boundary } from '../components/Boundary';
import { useApi } from '../contexts/ApiContext';
import { extractAvailableFields, mapFields } from '../functions/forms';
import { showApiErrorMessage } from '../functions/notifications';
import { hashString } from '../functions/tables';
import { useLocalState } from '../states/LocalState';
import { useUserSettingsState } from '../states/SettingsStates';
import { useStoredTableState } from '../states/StoredTableState';
import InvenTreeTableHeader from './InvenTreeTableHeader';

const ACTIONS_COLUMN_ACCESSOR: string = '--actions--';
const PAGE_SIZES = [10, 15, 20, 25, 50, 100, 500];

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
  printingAccessor: 'pk',
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
  const { userTheme } = useLocalState();

  const {
    pageSize,
    setPageSize,
    getHiddenColumns,
    setHiddenColumns,
    getTableColumnNames,
    setTableColumnNames,
    getTableSorting,
    setTableSorting
  } = useStoredTableState();

  const [fieldNames, setFieldNames] = useState<Record<string, string>>({});

  const api = useApi();
  const navigate = useNavigate();
  const { showContextMenu } = useContextMenu();

  const userSettings = useUserSettingsState();

  const stickyTableHeader = useMemo(() => {
    return userSettings.isSet('STICKY_TABLE_HEADER');
  }, [userSettings]);

  // Key used for caching table data
  const cacheKey = useMemo(() => {
    const key: string = `tbl-${tableState.tableKey}`;

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
    retry: 5,
    retryDelay: (attempt: number) => (1 + attempt) * 250,
    throwOnError: (error: any) => {
      showApiErrorMessage({
        error: error,
        title: t`Error loading table options`
      });

      return true;
    },
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
  }, []);

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

  // A hash of the current column configuration
  // This is a workaround to fix an issue with mantine-datatable where
  // the columns do not update correctly when they are changed dynamically
  // Ref: https://github.com/icflorescu/mantine-datatable/issues/759
  const [columnHash, setColumnHash] = useState<string>('');

  // Update column visibility when hiddenColumns change
  const dataColumns: any = useMemo(() => {
    let cols: TableColumn[] = columns.filter((col) => col?.hidden != true);

    cols = cols.map((col) => {
      // If the column is *not* switchable, it is always visible
      // Otherwise, check if it is "default hidden"

      const hidden: boolean =
        col.switchable == false
          ? false
          : (tableState.hiddenColumns?.includes(col.accessor) ?? false);

      return {
        ...col,
        hidden: hidden,
        resizable: col.resizable ?? true,
        title: col.title ?? fieldNames[col.accessor] ?? `${col.accessor}`,
        cellsStyle: (record: any, index: number) => {
          const width = (col as any).minWidth ?? 100;
          return {
            minWidth: width
          };
        },
        titleStyle: (record: any, index: number) => {
          const width = (col as any).minWidth ?? 100;
          return {
            minWidth: width
          };
        }
      };
    });

    // If row actions are available, add a column for them
    if (tableProps.rowActions) {
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

    const columnNames: string = cols.map((col) => col.accessor).join(',');
    setColumnHash(hashString(columnNames));

    return cols;
  }, [
    columns,
    fieldNames,
    tableProps.rowActions,
    tableState.hiddenColumns,
    tableState.selectedRecords
  ]);

  // Callback when column visibility is toggled
  const toggleColumn = useCallback(
    (columnName: string) => {
      const newColumns = [...dataColumns];

      const colIdx = newColumns.findIndex((col) => col.accessor == columnName);

      if (colIdx >= 0 && colIdx < newColumns.length) {
        newColumns[colIdx].hidden = !newColumns[colIdx].hidden;
      }

      const hiddenColumns = newColumns
        .filter((col) => col.hidden)
        .map((col) => col.accessor);

      tableState.setHiddenColumns(hiddenColumns);
      setHiddenColumns(cacheKey)(hiddenColumns);
    },
    [cacheKey, dataColumns]
  );

  // Final state of the table columns
  const tableColumns = useDataTableColumns({
    key: `${cacheKey}-${columnHash}`,
    columns: dataColumns,
    getInitialValueInEffect: false
  });

  // Reset the pagination state when the search term changes
  useEffect(() => {
    tableState.setPage(1);
    tableState.clearSelectedRecords();
  }, [
    tableState.searchTerm,
    tableState.filterSet.activeFilters,
    tableState.queryFilters
  ]);

  // Account for invalid page offsets
  useEffect(() => {
    if (
      tableState.page > 1 &&
      pageSize * (tableState.page - 1) > tableState.recordCount
    ) {
      tableState.setPage(1);
    } else if (tableState.page < 1) {
      tableState.setPage(1);
    }

    if (pageSize < 10) {
      // Default page size
      setPageSize(25);
    }
  }, [tableState.records, tableState.page, pageSize]);

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

      if (tableState.queryFilters && tableState.queryFilters.size > 0) {
        // Allow override of filters based on URL query parameters
        for (const [key, value] of tableState.queryFilters) {
          queryParams[key] = value;
        }
      } else if (tableState.filterSet.activeFilters) {
        // Use custom table filters only if not overridden by query parameters
        tableState.filterSet.activeFilters.forEach((flt) => {
          queryParams[flt.name] = flt.value;
        });
      }

      // Add custom search term
      if (tableState.searchTerm) {
        queryParams.search = tableState.searchTerm;
      }

      // Pagination
      if (tableProps.enablePagination && paginate) {
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
      sortStatus,
      tableProps.params,
      tableProps.enablePagination,
      tableState.filterSet.activeFilters,
      tableState.queryFilters,
      tableState.searchTerm,
      getOrderingTerm
    ]
  );

  const [cacheLoaded, setCacheLoaded] = useState<boolean>(false);

  useEffect(() => {
    const sorting: DataTableSortStatus = getTableSorting(cacheKey);

    if (sorting && !!sorting.columnAccessor && !!sorting.direction) {
      setSortStatus(sorting);
    }

    const hiddenColumns = getHiddenColumns(cacheKey);

    if (hiddenColumns == null) {
      // A "null" value indicates that the initial "hidden" columns have not been set
      const columnNames: string[] = columns
        .filter((col) => {
          // Find any switchable columns which are hidden by default
          return col.switchable != false && col.defaultVisible == false;
        })
        .map((col) => col.accessor);

      setHiddenColumns(cacheKey)(columnNames);
      tableState.setHiddenColumns(columnNames);
    } else {
      tableState.setHiddenColumns(hiddenColumns);
    }

    setCacheLoaded(true);
  }, [cacheKey]);

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

  const handleSortStatusChange = useCallback(
    (status: DataTableSortStatus<T>) => {
      tableState.setPage(1);
      setSortStatus(status);

      setTableSorting(cacheKey)(status);
    },
    [cacheKey]
  );

  // Function to perform API query to fetch required data
  const fetchTableData = async () => {
    const queryParams = getTableFilters(true);

    if (!url) {
      // No URL supplied - do not load!
      return [];
    }

    if (!cacheLoaded) {
      // Sorting not yet loaded - do not load!
      return [];
    }

    return api
      .get(url, {
        params: queryParams,
        timeout: 10 * 1000
      })
      .then((response) => {
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
      cacheLoaded,
      sortStatus.columnAccessor,
      sortStatus.direction,
      tableState.tableKey,
      tableState.filterSet.activeFilters,
      tableState.searchTerm
    ],
    retry: 5,
    retryDelay: (attempt: number) => (1 + attempt) * 250,
    throwOnError: (error: any) => {
      showApiErrorMessage({
        error: error,
        title: t`Error loading table data`
      });

      return true;
    },
    enabled: !!url && !tableData,
    queryFn: fetchTableData
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

  const tablePageSize = useMemo(() => {
    if (tableProps.enablePagination != false) {
      return pageSize;
    } else {
      return tableState.recordCount;
    }
  }, [tableProps.enablePagination, pageSize, tableState.recordCount]);

  // Update tableState.records when new data received
  useEffect(() => {
    tableState.setRecords(tableData ?? apiData ?? []);
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

    if (props.modelType && props.detailAction !== false) {
      // Add action to navigate to the detail view
      const accessor = props.modelField ?? 'pk';
      const pk = resolveItem(record, accessor);
      const url = getDetailUrl(props.modelType, pk);

      const model: string | undefined =
        ModelInformationDict[props.modelType]?.label?.();

      let detailsText: string = t`View details`;

      if (!!model) {
        detailsText = t`View ${model}`;
      }

      items.push({
        key: 'detail',
        title: detailsText,
        icon: <IconArrowRight />,
        onClick: (event: any) => {
          cancelEvent(event);
          navigateToLink(url, navigate, event);
        }
      });
    }

    return showContextMenu(items)(event);
  };

  // Pagination refresh table if pageSize changes
  const updatePageSize = useCallback((size: number) => {
    setPageSize(size);
    tableState.setPage(1);
    tableState.refreshTable();
  }, []);

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
        recordsPerPage: tablePageSize,
        page: Math.max(1, tableState.page),
        onPageChange: tableState.setPage,
        recordsPerPageOptions: PAGE_SIZES,
        onRecordsPerPageChange: updatePageSize
      };
    }

    return _params;
  }, [
    tablePageSize,
    tableProps.enablePagination,
    tableState.recordCount,
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
          <Boundary label={`InvenTreeTableHeader-${cacheKey}`}>
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
        <Boundary label={`InvenTreeTable-${cacheKey}`}>
          <Box pos='relative'>
            <DataTable
              style={{
                stickyHeader: stickyTableHeader ? 'top' : undefined
              }}
              height={stickyTableHeader ? '80vh' : undefined}
              withTableBorder={!tableProps.noHeader}
              withColumnBorders
              striped
              highlightOnHover
              loaderType={userTheme.loader}
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
