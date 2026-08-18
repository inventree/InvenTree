import type { ModelType } from '@lib/enums/ModelType';
import { create } from 'zustand';

type InstanceId = number | string;

/**
 * Context describing the "list" a detail view was opened from.
 *
 * When a user clicks a row in a table, we record the ordered list of
 * primary keys currently displayed (the filtered result set) and the
 * primary key that was clicked. The detail view header (PageDetail) then
 * uses this context to render "previous / next" navigation buttons.
 */
export interface TableNavigationContext {
  model: ModelType;
  records: InstanceId[];
  current: InstanceId;
}

interface TableNavigationStateProps {
  context: TableNavigationContext | null;
  setContext: (context: TableNavigationContext) => void;
  clearContext: () => void;
}

export const useTableNavigationState = create<TableNavigationStateProps>()(
  (set) => ({
    context: null,

    setContext: (context) => set({ context }),

    clearContext: () => set({ context: null })
  })
);

/**
 * Helper for setting the navigation context from outside of React
 * (e.g. inside a plain event handler in a table component).
 */
export function setTableNavigationContext(context: TableNavigationContext) {
  useTableNavigationState.getState().setContext(context);
}
