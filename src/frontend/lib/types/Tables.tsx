import type { MantineStyleProp } from '@mantine/core';
import type {
  DataTableCellClickHandler,
  DataTableRowExpansionProps
} from 'mantine-datatable';
import type { ReactNode } from 'react';
import type { NavigateFunction, SetURLSearchParams } from 'react-router-dom';
import type { ModelType } from '../enums/ModelType';
import type { FilterSetState, TableFilter } from './Filters';
import type { ApiFormFieldType } from './Forms';

/*
 * Type definition for representing the state of a table:
 *
 * tableKey: A unique key for the table. When this key changes, the table will be refreshed.
 * refreshTable: A callback function to externally refresh the table.
 * isLoading: A boolean flag to indicate if the table is currently loading data
 * setIsLoading: A function to set the isLoading flag
 * filterSet: A group of active filters
 * queryFilters: A map of query filters (e.g. ?active=true&overdue=false) passed in the URL
 * setQueryFilters: A function to set the query filters
 * clearQueryFilters: A function to clear all query filters
 * expandedRecords: An array of expanded records (rows) in the table
 * setExpandedRecords: A function to set the expanded records
 * isRowExpanded: A function to determine if a record is expanded
 * selectedRecords: An array of selected records (rows) in the table
 * selectedIds: An array of primary key values for selected records
 * hasSelectedRecords: A boolean flag to indicate if any records are selected
 * setSelectedRecords: A function to set the selected records
 * clearSelectedRecords: A function to clear all selected records
 * hiddenColumns: An array of hidden column names
 * setHiddenColumns: A function to set the hidden columns
 * searchTerm: The current search term for the table
 * setSearchTerm: A function to set the search term
 * recordCount: The total number of records in the table
 * setRecordCount: A function to set the record count
 * page: The current page number
 * setPage: A function to set the current page number
 * pageSize: The number of records per page
 * setPageSize: A function to set the number of records per page
 * records: An array of records (rows) in the table
 * setRecords: A function to set the records
 * updateRecord: A function to update a single record in the table
 * idAccessor: The name of the primary key field in the records (default = 'pk')
 */
export type TableState = {
  tableKey: string;
  refreshTable: (clearSelected?: boolean) => void;
  isLoading: boolean;
  setIsLoading: (value: boolean) => void;
  filterSet: FilterSetState;
  queryFilters: URLSearchParams;
  setQueryFilters: SetURLSearchParams;
  clearQueryFilters: () => void;
  expandedRecords: any[];
  setExpandedRecords: (records: any[]) => void;
  isRowExpanded: (pk: number) => boolean;
  selectedRecords: any[];
  selectedIds: any[];
  hasSelectedRecords: boolean;
  setSelectedRecords: (records: any[]) => void;
  clearSelectedRecords: () => void;
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  recordCount: number;
  setRecordCount: (count: number) => void;
  page: number;
  setPage: (page: number) => void;
  records: any[];
  setRecords: (records: any[]) => void;
  updateRecord: (record: any) => void;
  hiddenColumns: string[];
  setHiddenColumns: (columns: string[]) => void;
  idAccessor?: string;
};

/**
 * Table column properties
 *
 * @param T - The type of the record
 * @param accessor - The key in the record to access
 * @param title - The title of the column - Note: this may be supplied by the API, and is not required, but it can be overridden if required
 * @param ordering - The key in the record to sort by (defaults to accessor)
 * @param sortable - Whether the column is sortable
 * @param switchable - Whether the column is switchable
 * @param defaultVisible - Whether the column is visible by default (defaults to true)
 * @param hidden - Whether the column is hidden (forced hidden, cannot be toggled by the user))
 * @param editable - Whether the value of this column can be edited
 * @param definition - Optional field definition for the column
 * @param render - A custom render function
 * @param filter - A custom filter function
 * @param filtering - Whether the column is filterable
 * @param width - The width of the column
 * @param resizable - Whether the column is resizable (defaults to true)
 * @param noWrap - Whether the column should wrap
 * @param ellipsis - Whether the column should be ellipsized
 * @param textAlign - The text alignment of the column
 * @param cellsStyle - The style of the cells in the column
 * @param extra - Extra data to pass to the render function
 * @param noContext - Disable context menu for this column
 */
export type TableColumnProps<T = any> = {
  accessor?: string;
  title?: string;
  ordering?: string;
  sortable?: boolean;
  switchable?: boolean;
  hidden?: boolean;
  defaultVisible?: boolean;
  editable?: boolean;
  definition?: ApiFormFieldType;
  render?: (record: T, index?: number) => any;
  filter?: any;
  filtering?: boolean;
  width?: number;
  resizable?: boolean;
  noWrap?: boolean;
  ellipsis?: boolean;
  textAlign?: 'left' | 'center' | 'right';
  cellsStyle?: any;
  extra?: any;
  noContext?: boolean;
};

/**
 * Interface for the table column definition
 */
export type TableColumn<T = any> = {
  accessor: string; // The key in the record to access
} & TableColumnProps<T>;

// Type definition for a table row action
export type RowAction = {
  title?: string;
  tooltip?: string;
  color?: string;
  icon?: ReactNode;
  onClick?: (event: any) => void;
  hidden?: boolean;
  disabled?: boolean;
};

type RowModelProps = {
  modelType: ModelType;
  modelId: number;
  navigate: NavigateFunction;
};

export type RowViewProps = RowAction & RowModelProps;

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
 * @param printingAccessor : string - Accessor for label and report printing (default = 'pk')
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
  printingAccessor?: string;
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
  rowStyle?: (record: T, index: number) => MantineStyleProp | undefined;
  modelField?: string;
  onCellContextMenu?: (record: T, event: any) => void;
  minHeight?: number;
  noHeader?: boolean;
};
