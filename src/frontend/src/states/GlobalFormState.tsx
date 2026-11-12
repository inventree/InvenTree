/**
 * This file contains a global state manager for API form modals, allowing them to be opened and closed from anywhere in the app without needing to render the modal within the calling component.
 * This is primarily intended for use by plugins, which may need to launch a form from outside of a React component (e.g. from a primary action callback).
 * Each opened form is tracked as a separate entry, allowing multiple forms to be stacked (e.g. a form launched from within another form).
 * The `GlobalFormModals` component (rendered within the main layout) is responsible for rendering the open forms.
 */

import type { ApiFormModalProps } from '@lib/types/Forms';
import { create } from 'zustand';

export type GlobalFormType = 'create' | 'edit' | 'delete';

export interface GlobalFormEntry {
  id: string;
  formType: GlobalFormType;
  props: ApiFormModalProps;
  closeRequested: boolean;
}

interface GlobalFormStateProps {
  forms: GlobalFormEntry[];
  openForm: (formType: GlobalFormType, props: ApiFormModalProps) => string;
  closeForm: (id: string) => void;
  removeForm: (id: string) => void;
}

let formCounter = 0;

export const useGlobalFormState = create<GlobalFormStateProps>()(
  (set, get) => ({
    forms: [],

    openForm: (formType: GlobalFormType, props: ApiFormModalProps) => {
      // Always generate a unique ID, so that a form being removed cannot affect a newly opened form
      formCounter += 1;
      const id = `global-form-${formCounter}`;

      set({
        forms: [...get().forms, { id, formType, props, closeRequested: false }]
      });

      return id;
    },

    // Request that the form is closed - the modal is closed by the rendering component
    closeForm: (id: string) => {
      set({
        forms: get().forms.map((form) =>
          form.id === id ? { ...form, closeRequested: true } : form
        )
      });
    },

    // Remove the form entirely (once the modal has been closed)
    removeForm: (id: string) => {
      set({
        forms: get().forms.filter((form) => form.id !== id)
      });
    }
  })
);

export function openGlobalForm(
  formType: GlobalFormType,
  props: ApiFormModalProps
): string {
  return useGlobalFormState.getState().openForm(formType, props);
}

export function closeGlobalForm(id: string) {
  useGlobalFormState.getState().closeForm(id);
}
