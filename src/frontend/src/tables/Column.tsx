import type { ApiFormFieldType } from '../components/forms/fields/ApiFormField';

export type TableColumnProps<T = any> = {
  accessor?: string; // The key in the record to access
  title?: string; // The title of the column - Note: this may be supplied by the API, and is not required, but it can be overridden if required
  ordering?: string; // The key in the record to sort by (defaults to accessor)
  sortable?: boolean; // Whether the column is sortable
  switchable?: boolean; // Whether the column is switchable
  hidden?: boolean; // Whether the column is hidden
  editable?: boolean; // Whether the value of this column can be edited
  definition?: ApiFormFieldType; // Optional field definition for the column
  render?: (record: T, index?: number) => any; // A custom render function
  filter?: any; // A custom filter function
  filtering?: boolean; // Whether the column is filterable
  width?: number; // The width of the column
  noWrap?: boolean; // Whether the column should wrap
  ellipsis?: boolean; // Whether the column should be ellipsized
  textAlign?: 'left' | 'center' | 'right'; // The text alignment of the column
  cellsStyle?: any; // The style of the cells in the column
  extra?: any; // Extra data to pass to the render function
  noContext?: boolean; // Disable context menu for this column
};

/**
 * Interface for the table column definition
 */
export type TableColumn<T = any> = {
  accessor: string; // The key in the record to access
} & TableColumnProps<T>;
