/**
 * Interface for the table column definition
 */
export type TableColumn<T = any> = {
  accessor: string; // The key in the record to access
  ordering?: string; // The key in the record to sort by (defaults to accessor)
  title?: string; // The title of the column
  sortable?: boolean; // Whether the column is sortable
  switchable?: boolean; // Whether the column is switchable
  hidden?: boolean; // Whether the column is hidden
  render?: (record: T) => any; // A custom render function
  filter?: any; // A custom filter function
  filtering?: boolean; // Whether the column is filterable
  width?: number; // The width of the column
  noWrap?: boolean; // Whether the column should wrap
  ellipsis?: boolean; // Whether the column should be ellipsized
  textAlignment?: 'left' | 'center' | 'right'; // The text alignment of the column
  cellsStyle?: any; // The style of the cells in the column
};
