import type { ModelType } from '@lib/enums/ModelType';
import { create } from 'zustand';

interface PreviewDrawerStateProps {
  isOpen: boolean;
  modelType?: ModelType;
  instance?: any;
  openPreview: (modelType: ModelType, instance: any) => void;
  closePreview: () => void;
}

export const usePreviewDrawerState = create<PreviewDrawerStateProps>()(
  (set) => ({
    isOpen: false,
    instance: null,

    openPreview: (modelType: ModelType, instance: any) => {
      set({ modelType, instance, isOpen: true });
    },

    closePreview: () => {
      set({ modelType: undefined, instance: null, isOpen: false });
    }
  })
);

export function openGlobalPreview(modelType: ModelType, instance: any) {
  usePreviewDrawerState.getState().openPreview(modelType, instance);
}

export function closeGlobalPreview() {
  usePreviewDrawerState.getState().closePreview();
}

export function getGlobalPreviewState() {
  return usePreviewDrawerState.getState();
}
