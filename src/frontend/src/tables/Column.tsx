import type { ApiFormFieldType } from '@lib/types/Forms';

/**
 * Table column properties
 *
 * @param T - The type of the record
 * @param accessor - The key in the record to access
 * @param title - The title of the column - Note: this may be supplied by the API, and is not required, but it can be overridden if required
 * @param ordering - The key in the record to sort by (defaults to accessor)
 * @param sortable - Whether the column is sortable
 * @param switchable - Whether the column is switchable
 * @param hidden - Whether the column is hidden
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
