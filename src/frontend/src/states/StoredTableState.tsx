import type { DataTableSortStatus } from 'mantine-datatable';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const DEFAULT_PAGE_SIZE: number = 25;

/**
 * Interfacing for storing persistent table state in the browser.
 *
 * The following properties are stored:
 * - pageSize: The number of rows to display per page in the table.
 * - hiddenColumns: An array of column names that are hidden in a given table.
 * - columnNames: An object mapping table keys to arrays of column names.
 * - sorting: An object mapping table keys to sorting configurations.
 */
interface StoredTableStateProps {
  pageSize: number;
  setPageSize: (size: number) => void;
  tableSorting: Record<string, any>;
  getTableSorting: (tableKey: string) => DataTableSortStatus;
  setTableSorting: (
    tableKey: string
  ) => (sorting: DataTableSortStatus<any>) => void;
  tableColumnNames: Record<string, Record<string, string>>;
  getTableColumnNames: (tableKey: string) => Record<string, string>;
  setTableColumnNames: (
    tableKey: string
  ) => (names: Record<string, string>) => void;
  clearTableColumnNames: () => void;
  hiddenColumns: Record<string, string[]>;
  getHiddenColumns: (tableKey: string) => string[] | null;
  setHiddenColumns: (tableKey: string) => (columns: string[]) => void;
}

export const useStoredTableState = create<StoredTableStateProps>()(
  persist(
    (set, get) => ({
      pageSize: DEFAULT_PAGE_SIZE,
      setPageSize: (size: number) => {
        set((state) => ({
          pageSize: size
        }));
      },
      tableSorting: {},
      getTableSorting: (tableKey) => {
        return get().tableSorting[tableKey] || {};
      },
      setTableSorting: (tableKey) => (sorting) => {
        // Update the table sorting for the given table
        set({
          tableSorting: {
            ...get().tableSorting,
            [tableKey]: sorting
          }
        });
      },
      tableColumnNames: {},
      getTableColumnNames: (tableKey) => {
        return get().tableColumnNames[tableKey] || null;
      },
      setTableColumnNames: (tableKey) => (names) => {
        // Update the table column names for the given table
        set({
          tableColumnNames: {
            ...get().tableColumnNames,
            [tableKey]: names
          }
        });
      },
      clearTableColumnNames: () => {
        set({ tableColumnNames: {} });
      },
      hiddenColumns: {},
      getHiddenColumns: (tableKey) => {
        return get().hiddenColumns?.[tableKey] ?? null;
      },
      setHiddenColumns: (tableKey) => (columns) => {
        // Update the hidden columns for the given table
        set({
          hiddenColumns: {
            ...get().hiddenColumns,
            [tableKey]: columns
          }
        });
      }
    }),
    {
      name: 'inventree-table-state'
    }
  )
);
