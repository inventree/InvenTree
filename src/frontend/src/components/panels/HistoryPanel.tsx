import { t } from '@lingui/core/macro';
import { Skeleton } from '@mantine/core';
import { IconHistory } from '@tabler/icons-react';
import { useMemo } from 'react';

import type { ModelType } from '@lib/enums/ModelType';
import type { PanelType } from '@lib/types/Panel';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../../states/SettingsStates';
import { AuditLogTable } from '../../tables/general/AuditLogTable';

/**
 * Determine whether the history panel should be displayed on detail pages:
 * - The audit log must be enabled
 * - Must be enabled via the 'DISPLAY_HISTORY_TAB' user setting
 *
 * Note: The displayed entries are filtered by the permissions of the user
 */
export function useShowHistoryPanel(): boolean {
  const userSettings = useUserSettingsState();
  const globalSettings = useGlobalSettingsState();

  return useMemo(
    () =>
      globalSettings.isSet('AUDIT_LOG_ENABLED') &&
      userSettings.isSet('DISPLAY_HISTORY_TAB', false),
    [userSettings, globalSettings]
  );
}

/**
 * Panel displaying the audit log (change history) for a model instance.
 * Only add this panel to detail pages for models which are audited,
 * and pass the result of useShowHistoryPanel() as 'visible'.
 */
export default function HistoryPanel({
  model_type,
  model_id,
  visible
}: {
  model_type: ModelType;
  model_id: number | undefined;
  visible: boolean;
}): PanelType {
  return {
    name: 'history',
    label: t`History`,
    icon: <IconHistory />,
    hidden: !visible,
    content:
      visible && model_type && model_id ? (
        <AuditLogTable modelType={model_type} modelId={model_id} />
      ) : (
        <Skeleton />
      )
  };
}
