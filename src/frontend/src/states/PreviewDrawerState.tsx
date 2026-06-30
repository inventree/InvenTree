import type { ModelType } from '@lib/enums/ModelType';
import { create } from 'zustand';
import type { PreviewType } from '../components/previews/PreviewType';

interface PreviewDrawerStateProps {
  isOpen: boolean;
  modelType?: ModelType;
  id?: number | string;
  instance?: any;
  preview?: PreviewType;
  openPreview: (
    modelType: ModelType,
    id: number | string | undefined,
    instance?: any,
    preview?: PreviewType
  ) => void;
  closePreview: () => void;
}

export const usePreviewDrawerState = create<PreviewDrawerStateProps>()(
  (set) => ({
    isOpen: false,
    modelType: undefined,
    id: undefined,
    instance: undefined,
    preview: undefined,

    openPreview: (
      modelType: ModelType,
      id: number | string | undefined,
      instance?: any,
      preview?: PreviewType
    ) => {
      set({ modelType, id, instance, preview, isOpen: true });
    },

    closePreview: () => {
      set({ isOpen: false });
    }
  })
);

export function openGlobalPreview(
  modelType: ModelType,
  id?: number | string | undefined,
  instance?: any,
  preview?: PreviewType
) {
  usePreviewDrawerState
    .getState()
    .openPreview(modelType, id, instance, preview);
}

export function closeGlobalPreview() {
  usePreviewDrawerState.getState().closePreview();
}

export function getGlobalPreviewState() {
  return usePreviewDrawerState.getState();
}
