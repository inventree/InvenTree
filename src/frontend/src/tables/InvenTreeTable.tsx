import { t } from '@lingui/macro';
import {
  ActionIcon,
  Alert,
  Box,
  Group,
  Indicator,
  LoadingOverlay,
  Space,
  Stack,
  Tooltip
} from '@mantine/core';
import {
  IconBarcode,
  IconFilter,
  IconRefresh,
  IconTrash
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import {
  DataTable,
  DataTableCellClickHandler,
  DataTableSortStatus
} from 'mantine-datatable';
import React, {
  Fragment,
  useCallback,
  useEffect,
  useMemo,
  useState
} from 'react';
import { useNavigate } from 'react-router-dom';

import { api } from '../App';
import { Boundary } from '../components/Boundary';
import { ActionButton } from '../components/buttons/ActionButton';
import { ButtonMenu } from '../components/buttons/ButtonMenu';
import { PrintingActions } from '../components/buttons/PrintingActions';
import { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';
import { ModelType } from '../enums/ModelType';
import { resolveItem } from '../functions/conversion';
import { cancelEvent } from '../functions/events';
import { extractAvailableFields, mapFields } from '../functions/forms';
import { navigateToLink } from '../functions/navigation';
import { getDetailUrl } from '../functions/urls';
import { useDeleteApiFormModal } from '../hooks/UseForm';
import { TableState } from '../hooks/UseTable';
import { useLocalState } from '../states/LocalState';
import { TableColumn } from './Column';
import { TableColumnSelect } from './ColumnSelect';
import { DownloadAction } from './DownloadAction';
import { TableFilter } from './Filter';
import { FilterSelectDrawer } from './FilterSelectDrawer';
import { RowAction, RowActions } from './RowActions';
import { TableSearchInput } from './Search';

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
  rowExpansion?: any;
  idAccessor?: string;
  dataFormatter?: (data: any) => any;
  rowActions?: (record: T) => RowAction[];
  onRowClick?: (record: T, index: number, event: any) => void;
  onCellClick?: DataTableCellClickHandler<T>;
  modelType?: ModelType;
  rowStyle?: (record: T, index: number) => any;
  modelField?: string;
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
  tableActions: [],
  idAccessor: 'pk'
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
  const {
    getTableColumnNames,
    setTableColumnNames,
    getTableSorting,
    setTableSorting
  } = useLocalState();
  const [fieldNames, setFieldNames] = useState<Record<string, string>>({});

  const navigate = useNavigate();

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
    enabled: true,
    queryKey: ['options', url, tableState.tableKey, props.enableColumnCaching],
    retry: 3,
    refetchOnMount: true,
    queryFn: async () => {
      if (props.enableColumnCaching == false) {
        return null;
      }
      return api
        .options(url, {
          params: tableProps.params
        })
        .then((response) => {
          if (response.status == 200) {
            // Extract field information from the API

            let names: Record<string, string> = {};
            let fields: ApiFormFieldSet =
              extractAvailableFields(response, 'POST', true) || {};

            // Extract flattened map of fields
            mapFields(fields, (path, field) => {
              if (field.label) {
                names[path] = field.label;
              }
            });

            const cacheKey = tableState.tableKey.split('-')[0];

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

    const cacheKey = tableState.tableKey.split('-')[0];

    // First check the local cache
    const cachedNames = getTableColumnNames(cacheKey);

    if (Object.keys(cachedNames).length > 0) {
      // Cached names are available - use them!
      setFieldNames(cachedNames);
      return;
    }

    // Otherwise, fetch the data from the API
    tableOptionQuery.refetch();
  }, [url, tableState.tableKey, props.params, props.enableColumnCaching]);

  // Build table properties based on provided props (and default props)
  const tableProps: InvenTreeTableProps<T> = useMemo(() => {
    return {
      ...defaultInvenTreeTableProps,
      ...props
    };
  }, [props]);

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
    let cols = columns
      .filter((col) => col?.hidden != true)
      .map((col) => {
        let hidden: boolean = col.hidden ?? false;

        if (col.switchable ?? true) {
          hidden = tableState.hiddenColumns.includes(col.accessor);
        }

        return {
          ...col,
          hidden: hidden,
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

  // Filter list visibility
  const [filtersVisible, setFiltersVisible] = useState<boolean>(false);

  // Reset the pagination state when the search term changes
  useEffect(() => {
    tableState.setPage(1);
  }, [tableState.searchTerm]);

  /*
   * Construct query filters for the current table
   */
  function getTableFilters(paginate: boolean = false) {
    let queryParams = {
      ...tableProps.params
    };

    // Add custom filters
    if (tableState.activeFilters) {
      tableState.activeFilters.forEach(
        (flt) => (queryParams[flt.name] = flt.value)
      );
    }

    // Add custom search term
    if (tableState.searchTerm) {
      queryParams.search = tableState.searchTerm;
    }

    // Pagination
    if (tableProps.enablePagination && paginate) {
      let pageSize = tableState.pageSize ?? defaultPageSize;
      if (pageSize != tableState.pageSize) tableState.setPageSize(pageSize);
      queryParams.limit = pageSize;
      queryParams.offset = (tableState.page - 1) * pageSize;
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

  useEffect(() => {
    const tableKey: string = tableState.tableKey.split('-')[0];
    const sorting: DataTableSortStatus = getTableSorting(tableKey);

    if (sorting) {
      setSortStatus(sorting);
    }
  }, []);

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
    tableState.setPage(1);
    setSortStatus(status);

    const tableKey = tableState.tableKey.split('-')[0];
    setTableSorting(tableKey)(status);
  };

  // Function to perform API query to fetch required data
  const fetchTableData = async () => {
    let queryParams = getTableFilters(true);

    return api
      .get(url, {
        params: queryParams,
        timeout: 5 * 1000
      })
      .then(function (response) {
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
      tableState.page,
      props.params,
      sortStatus.columnAccessor,
      sortStatus.direction,
      tableState.tableKey,
      tableState.activeFilters,
      tableState.searchTerm
    ],
    queryFn: fetchTableData,
    refetchOnMount: true
  });

  useEffect(() => {
    tableState.setIsLoading(isFetching);
  }, [isFetching]);

  // Update tableState.records when new data received
  useEffect(() => {
    tableState.setRecords(data ?? []);
  }, [data]);

  const deleteRecords = useDeleteApiFormModal({
    url: url,
    title: t`Delete Selected Items`,
    preFormContent: (
      <Alert
        color="red"
        title={t`Are you sure you want to delete the selected items?`}
      >
        {t`This action cannot be undone!`}
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

      if (props.afterBulkDelete) {
        props.afterBulkDelete();
      }
    }
  });

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
          let url = getDetailUrl(tableProps.modelType, pk);
          navigateToLink(url, navigate, event);
        }
      }
    },
    [props.onRowClick, props.onCellClick]
  );

  // pagination refresth table if pageSize changes
  function updatePageSize(newData: number) {
    tableState.setPageSize(newData);
    tableState.setPage(1);
    tableState.refreshTable();
  }

  return (
    <>
      {deleteRecords.modal}
      {tableProps.enableFilters && (filters.length ?? 0) > 0 && (
        <Boundary label="table-filter-drawer">
          <FilterSelectDrawer
            availableFilters={filters}
            tableState={tableState}
            opened={filtersVisible}
            onClose={() => setFiltersVisible(false)}
          />
        </Boundary>
      )}
      <Boundary label={`InvenTreeTable-${tableState.tableKey}`}>
        <Stack gap="sm">
          <Group justify="apart" grow wrap="nowrap">
            <Group justify="left" key="custom-actions" gap={5} wrap="nowrap">
              <PrintingActions
                items={tableState.selectedIds}
                modelType={tableProps.modelType}
                enableLabels={tableProps.enableLabels}
                enableReports={tableProps.enableReports}
              />
              {(tableProps.barcodeActions?.length ?? 0) > 0 && (
                <ButtonMenu
                  key="barcode-actions"
                  icon={<IconBarcode />}
                  label={t`Barcode actions`}
                  tooltip={t`Barcode actions`}
                  actions={tableProps.barcodeActions ?? []}
                />
              )}
              {(tableProps.enableBulkDelete ?? false) && (
                <ActionButton
                  disabled={!tableState.hasSelectedRecords}
                  icon={<IconTrash />}
                  color="red"
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
            <Group justify="right" gap={5} wrap="nowrap">
              {tableProps.enableSearch && (
                <TableSearchInput
                  searchCallback={(term: string) =>
                    tableState.setSearchTerm(term)
                  }
                />
              )}
              {tableProps.enableRefresh && (
                <ActionIcon variant="transparent" aria-label="table-refresh">
                  <Tooltip label={t`Refresh data`}>
                    <IconRefresh
                      onClick={() => {
                        refetch();
                        tableState.clearSelectedRecords();
                      }}
                    />
                  </Tooltip>
                </ActionIcon>
              )}
              {hasSwitchableColumns && (
                <TableColumnSelect
                  columns={dataColumns}
                  onToggleColumn={toggleColumn}
                />
              )}
              {tableProps.enableFilters && filters.length > 0 && (
                <Indicator
                  size="xs"
                  label={tableState.activeFilters?.length ?? 0}
                  disabled={tableState.activeFilters?.length == 0}
                >
                  <ActionIcon
                    variant="transparent"
                    aria-label="table-select-filters"
                  >
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
          <Box pos="relative">
            <LoadingOverlay
              visible={
                tableOptionQuery.isLoading || tableOptionQuery.isFetching
              }
            />

            <DataTable
              withTableBorder
              withColumnBorders
              striped
              highlightOnHover
              loaderType="dots"
              pinLastColumn={tableProps.rowActions != undefined}
              idAccessor={tableProps.idAccessor}
              minHeight={300}
              totalRecords={tableState.recordCount}
              recordsPerPage={tableState.pageSize}
              page={tableState.page}
              onPageChange={tableState.setPage}
              sortStatus={sortStatus}
              onSortStatusChange={handleSortStatusChange}
              selectedRecords={
                tableProps.enableSelection
                  ? tableState.selectedRecords
                  : undefined
              }
              onSelectedRecordsChange={
                tableProps.enableSelection ? onSelectedRecordsChange : undefined
              }
              rowExpansion={tableProps.rowExpansion}
              rowStyle={tableProps.rowStyle}
              fetching={isFetching}
              noRecordsText={missingRecordsText}
              records={tableState.records}
              columns={dataColumns}
              onCellClick={handleCellClick}
              defaultColumnProps={{
                noWrap: true,
                textAlign: 'left',
                cellsStyle: () => (theme) => ({
                  // TODO @SchrodingersGat : Need a better way of handling "wide" cells,
                  overflow: 'hidden'
                })
              }}
              recordsPerPageOptions={PAGE_SIZES}
              onRecordsPerPageChange={updatePageSize}
            />
          </Box>
        </Stack>
      </Boundary>
    </>
  );
}
