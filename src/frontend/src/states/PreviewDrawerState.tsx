import type { ModelType } from '@lib/enums/ModelType';
import { create } from 'zustand';

interface PreviewDrawerStateProps {
  isOpen: boolean;
  modelType?: ModelType;
  id?: number | string;
  instance?: any;
  openPreview: (
    modelType: ModelType,
    id: number | string | undefined,
    instance?: any
  ) => void;
  closePreview: () => void;
}

export const usePreviewDrawerState = create<PreviewDrawerStateProps>()(
  (set) => ({
    isOpen: false,
    modelType: undefined,
    id: undefined,
    instance: undefined,

    openPreview: (
      modelType: ModelType,
      id: number | string | undefined,
      instance?: any
    ) => {
      set({ modelType, id, instance, isOpen: true });
    },

    closePreview: () => {
      set({ isOpen: false });
    }
  })
);

export function openGlobalPreview(
  modelType: ModelType,
  id?: number | string | undefined,
  instance?: any
) {
  usePreviewDrawerState.getState().openPreview(modelType, id, instance);
}

export function closeGlobalPreview() {
  usePreviewDrawerState.getState().closePreview();
}

export function getGlobalPreviewState() {
  return usePreviewDrawerState.getState();
}
