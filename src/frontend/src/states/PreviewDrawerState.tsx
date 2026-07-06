import type { ModelType } from '@lib/enums/ModelType';
import { create } from 'zustand';
import type { PreviewType } from '../components/previews/PreviewType';

type PreviewDrawerId = number | string | undefined;

interface PreviewDrawerStateProps {
  isOpen: boolean;
  modelType?: ModelType;
  id?: number | string;
  instance?: any;
  preview?: PreviewType;
  targetUrl?: string;
  onCloseCallback?: () => void;
  openPreview: (
    modelType: ModelType,
    id: PreviewDrawerId,
    instance?: any,
    preview?: PreviewType,
    onClose?: () => void,
    targetUrl?: string
  ) => void;
  closePreview: () => void;
}

export const usePreviewDrawerState = create<PreviewDrawerStateProps>()(
  (set, get) => ({
    isOpen: false,
    modelType: undefined,
    id: undefined,
    instance: undefined,
    preview: undefined,
    targetUrl: undefined,
    onCloseCallback: undefined,

    openPreview: (
      modelType: ModelType,
      id: number | string | undefined,
      instance?: any,
      preview?: PreviewType,
      onClose?: () => void,
      targetUrl?: string
    ) => {
      set({
        modelType,
        id,
        instance,
        preview,
        targetUrl,
        isOpen: true,
        onCloseCallback: onClose
      });
    },

    closePreview: () => {
      const callback = get().onCloseCallback;

      set({
        isOpen: false,
        instance: undefined,
        id: undefined,
        preview: undefined,
        targetUrl: undefined,
        onCloseCallback: undefined
      });

      callback?.();
    }
  })
);

export function openGlobalPreview(
  modelType: ModelType,
  id?: number | string | undefined,
  instance?: any,
  preview?: PreviewType,
  onClose?: () => void,
  targetUrl?: string
) {
  usePreviewDrawerState
    .getState()
    .openPreview(modelType, id, instance, preview, onClose, targetUrl);
}

export function closeGlobalPreview() {
  usePreviewDrawerState.getState().closePreview();
}

export function getGlobalPreviewState() {
  return usePreviewDrawerState.getState();
}
