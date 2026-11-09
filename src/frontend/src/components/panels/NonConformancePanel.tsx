import { t } from '@lingui/core/macro';
import { Skeleton } from '@mantine/core';
import { IconAlertTriangle } from '@tabler/icons-react';

import type { PanelType } from '@lib/types/Panel';
import { NonConformanceTable } from '../../tables/build/NonConformanceTable';

/**
 * Panel displaying the NonConformance (NCR) reports linked to a particular record.
 * Exactly one of the record ID props should be provided (stockItemId may be combined with partId).
 * Pass !user.hasViewVisible(UserRoles.ncr) as 'hidden'.
 */
export default function NonConformancePanel({
  hidden,
  partId,
  buildOrderId,
  salesOrderId,
  purchaseOrderId,
  returnOrderId,
  stockItemId
}: {
  hidden: boolean;
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
    hidden: hidden,
    content: recordId ? (
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
