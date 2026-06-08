import { usePreviewDrawerState } from '../../states/PreviewDrawerState';
import PreviewDrawer from './PreviewDrawer';

export default function GlobalPreviewDrawer() {
  const isOpen = usePreviewDrawerState((state) => state.isOpen);
  const modelType = usePreviewDrawerState((state) => state.modelType);
  const id = usePreviewDrawerState((state) => state.id);
  const instance = usePreviewDrawerState((state) => state.instance);
  const closePreview = usePreviewDrawerState((state) => state.closePreview);

  // Only skip rendering before the drawer has ever been opened
  if (modelType === undefined || id === undefined) {
    return null;
  }

  return (
    <PreviewDrawer
      modelType={modelType}
      id={id}
      instance={instance}
      opened={isOpen}
      onClose={closePreview}
    />
  );
}
