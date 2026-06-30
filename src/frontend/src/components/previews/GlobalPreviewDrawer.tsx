import { usePreviewDrawerState } from '../../states/PreviewDrawerState';
import PreviewDrawer from './PreviewDrawer';

export default function GlobalPreviewDrawer() {
  const isOpen = usePreviewDrawerState((state) => state.isOpen);
  const modelType = usePreviewDrawerState((state) => state.modelType);
  const id = usePreviewDrawerState((state) => state.id);
  const instance = usePreviewDrawerState((state) => state.instance);
  const preview = usePreviewDrawerState((state) => state.preview);
  const closePreview = usePreviewDrawerState((state) => state.closePreview);

  return (
    <PreviewDrawer
      modelType={modelType}
      id={id}
      instance={instance}
      preview={preview}
      opened={isOpen}
      onClose={closePreview}
    />
  );
}
