import { usePreviewDrawerState } from '../../states/PreviewDrawerState';
import PreviewDrawer from './PreviewDrawer';

export default function GlobalPreviewDrawer() {
  const isOpen = usePreviewDrawerState((state) => state.isOpen);
  const modelType = usePreviewDrawerState((state) => state.modelType);
  const instance = usePreviewDrawerState((state) => state.instance);
  const closePreview = usePreviewDrawerState((state) => state.closePreview);

  if (!isOpen || instance === null) {
    return null;
  }

  return (
    <PreviewDrawer
      modelType={modelType}
      instance={instance}
      opened={isOpen}
      onClose={closePreview}
    />
  );
}
