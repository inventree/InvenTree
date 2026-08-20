/**
 * This file contains a global state manager for the importer drawer, allowing it to be opened and closed from anywhere in the app without needing to pass props down through the component tree.
 * The state includes the current session ID for the importer, as well as an optional callback function that can be executed when the importer is closed.
 * This allows for flexible handling of importer actions, such as refreshing data after an import is completed.
 * The state is managed using the Zustand library, which provides a simple and efficient way to create global state in React applications.
 * The `useImporterState` hook can be used to access and manipulate the importer state from any component, while the `openGlobalImporter` and `closeGlobalImporter` functions provide convenient ways to control the importer from outside of React components.
 */

import type { ApiFormFieldSet } from '@lib/index';
import { create } from 'zustand';

export interface ImporterOpenOptions {
  fields?: ApiFormFieldSet | null;
  onClose?: () => void;
}

interface ImporterStateProps {
  isOpen: boolean;
  sessionId: number | null;
  customFields?: ApiFormFieldSet | null;
  onCloseCallback?: () => void;
  openImporter: (sessionId: number, options?: ImporterOpenOptions) => void;
  closeImporter: () => void;
}

export const useImporterState = create<ImporterStateProps>()((set, get) => ({
  isOpen: false,
  sessionId: null,
  customFields: null,
  onCloseCallback: undefined,

  openImporter: (sessionId: number, options?: ImporterOpenOptions) => {
    set({
      sessionId,
      isOpen: true,
      customFields: options?.fields ?? null,
      onCloseCallback: options?.onClose
    });
  },

  closeImporter: () => {
    const callback = get().onCloseCallback;

    set({
      sessionId: null,
      isOpen: false,
      customFields: null,
      onCloseCallback: undefined
    });

    callback?.();
  }
}));

export function openGlobalImporter(
  sessionId: number,
  options?: ImporterOpenOptions
) {
  useImporterState.getState().openImporter(sessionId, options);
}

export function closeGlobalImporter() {
  useImporterState.getState().closeImporter();
}

export function getGlobalImporterState() {
  return useImporterState.getState();
}
