import { usePreviewDrawerState } from '../../states/PreviewDrawerState';
import { useUserSettingsState } from '../../states/SettingsStates';
import PreviewDrawer from './PreviewDrawer';

export default function GlobalPreviewDrawer() {
  const enabled = useUserSettingsState((state) =>
    state.isSet('ENABLE_PREVIEW_PANEL')
  );

  const drawer = usePreviewDrawerState((state) => state);

  if (!enabled) {
    return null;
  }

  return (
    <PreviewDrawer
      modelType={drawer.modelType}
      id={drawer.id}
      instance={drawer.instance}
      filters={drawer.filters}
      preview={drawer.preview}
      targetUrl={drawer.targetUrl}
      opened={drawer.isOpen}
      onClose={drawer.closePreview}
    />
  );
}
