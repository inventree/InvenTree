import type { SetURLSearchParams } from 'react-router-dom';
import type { FilterSetState } from './Filters';

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
