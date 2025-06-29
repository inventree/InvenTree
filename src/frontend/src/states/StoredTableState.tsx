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
}

export const useStoredTableState = create<StoredTableStateProps>()(
  persist(
    (set, get) => ({
      pageSize: DEFAULT_PAGE_SIZE,
      setPageSize: (size: number) => {
        set((state) => ({
          pageSize: size
        }));
      }
    }),
    {
      name: 'inventree-table-state'
    }
  )
);
