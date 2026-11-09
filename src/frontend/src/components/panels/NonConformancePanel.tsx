import { t } from '@lingui/core/macro';
import { Skeleton } from '@mantine/core';
import { IconAlertTriangle } from '@tabler/icons-react';
import { useMemo } from 'react';

import { UserRoles } from '@lib/enums/Roles';
import type { PanelType } from '@lib/types/Panel';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';
import { NonConformanceTable } from '../../tables/build/NonConformanceTable';

/**
 * Determine whether linked NCRs should be displayed on detail pages (outside the manufacturing index):
 * - NCR functionality must be enabled, and the user must have the 'ncr' view role
 * - Must be enabled via the 'DISPLAY_NCR_EXTENDED_VIEWS' user setting
 */
export function useShowNonConformancePanel(): boolean {
  const user = useUserState();
  const userSettings = useUserSettingsState();
  const globalSettings = useGlobalSettingsState();

  return useMemo(
    () =>
      user.hasViewVisible(UserRoles.ncr) &&
      userSettings.isSet('DISPLAY_NCR_EXTENDED_VIEWS', false),
    [user, userSettings, globalSettings]
  );
}

/**
 * Panel displaying the NonConformance (NCR) reports linked to a particular record.
 * Exactly one of the record ID props should be provided (stockItemId may be combined with partId).
 * Pass the result of useShowNonConformancePanel() as 'visible'.
 */
export default function NonConformancePanel({
  visible,
  partId,
  buildOrderId,
  salesOrderId,
  purchaseOrderId,
  returnOrderId,
  stockItemId
}: {
  visible: boolean;
  partId?: number;
  buildOrderId?: number;
  salesOrderId?: number;
  purchaseOrderId?: number;
  returnOrderId?: number;
  stockItemId?: number;
}): PanelType {
  // Do not render the table until the linked record is known,
  // otherwise the (unfiltered) list of all NCRs would be displayed
  const recordId =
    stockItemId ??
    buildOrderId ??
    salesOrderId ??
    purchaseOrderId ??
    returnOrderId ??
    partId;

  return {
    name: 'non-conformances',
    label: t`Non-Conformances`,
    icon: <IconAlertTriangle />,
    hidden: !visible,
    content:
      visible && recordId ? (
        <NonConformanceTable
          partId={partId}
          buildOrderId={buildOrderId}
          salesOrderId={salesOrderId}
          purchaseOrderId={purchaseOrderId}
          returnOrderId={returnOrderId}
          stockItemId={stockItemId}
        />
      ) : (
        <Skeleton />
      )
  };
}
