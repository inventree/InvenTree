import { usePreviewDrawerState } from '../../states/PreviewDrawerState';
import { useUserSettingsState } from '../../states/SettingsStates';
import PreviewDrawer from './PreviewDrawer';

export default function GlobalPreviewDrawer() {
  const enabled = useUserSettingsState((state) =>
    state.isSet('ENABLE_PREVIEW_PANEL')
  );
  const isOpen = usePreviewDrawerState((state) => state.isOpen);
  const modelType = usePreviewDrawerState((state) => state.modelType);
  const id = usePreviewDrawerState((state) => state.id);
  const instance = usePreviewDrawerState((state) => state.instance);
  const preview = usePreviewDrawerState((state) => state.preview);
  const targetUrl = usePreviewDrawerState((state) => state.targetUrl);
  const closePreview = usePreviewDrawerState((state) => state.closePreview);

  if (!enabled) {
    return null;
  }

  return (
    <PreviewDrawer
      modelType={modelType}
      id={id}
      instance={instance}
      preview={preview}
      targetUrl={targetUrl}
      opened={isOpen}
      onClose={closePreview}
    />
  );
}
