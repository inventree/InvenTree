import {
  type RowAction,
  RowViewAction,
  type RowViewProps
} from '@lib/components/RowActions';

import { openGlobalPreview } from '../../states/PreviewDrawerState';
import { useUserSettingsState } from '../../states/SettingsStates';

/*
 * An internal wrapper for the RowViewAction component, which adds support for the global preview panel.
 */
export function AppRowViewAction(props: RowViewProps): RowAction {
  return RowViewAction({
    ...props,
    isPreviewEnabled: () =>
      useUserSettingsState.getState().isSet('ENABLE_PREVIEW_PANEL'),
    openPreview: (modelType, modelId) => {
      openGlobalPreview(modelType, modelId);
    }
  });
}
