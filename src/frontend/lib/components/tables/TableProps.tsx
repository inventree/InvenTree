import type { ModelType } from '@lib/core';
import type {
  DataTableCellClickHandler,
  DataTableRowExpansionProps
} from 'mantine-datatable';
import type { TableFilter } from './Filter';
import type { RowAction } from './RowAction';

export const TABLE_PAGE_SIZE_DEFAULT: number = 25;
export const TABLE_PAGE_SIZE_OPTIONS: number[] = [10, 15, 20, 25, 50, 100, 500];

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
