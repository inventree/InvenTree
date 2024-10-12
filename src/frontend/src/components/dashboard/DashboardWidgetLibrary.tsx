import { t } from '@lingui/macro';

import { ModelType } from '../../enums/ModelType';
import { DashboardWidgetProps } from './DashboardWidget';
import QueryCountDashboardWidget from './widgets/QueryCountDashboardWidget';

/**
 *
 * @returns A list of built-in dashboard widgets which display the number of results for a particular query
 */
export function BuiltinQueryCountWidgets(): DashboardWidgetProps[] {
  return [
    QueryCountDashboardWidget({
      title: t`Subscribed Parts`,
      modelType: ModelType.part,
      params: { starred: true }
    }),
    QueryCountDashboardWidget({
      title: t`Subscribed Categories`,
      modelType: ModelType.partcategory,
      params: { starred: true }
    }),
    // TODO: 'latest parts'
    // TODO: 'BOM waiting validation'
    // TODO: 'recently updated stock'
    QueryCountDashboardWidget({
      title: t`Low Stock`,
      modelType: ModelType.part,
      params: { low_stock: true }
    }),
    // TODO: Required for build orders
    QueryCountDashboardWidget({
      title: t`Expired Stock Items`,
      modelType: ModelType.stockitem,
      params: { expired: true }
      // TODO: Hide if expiry is disabled
    }),
    QueryCountDashboardWidget({
      title: t`Stale Stock Items`,
      modelType: ModelType.stockitem,
      params: { stale: true }
      // TODO: Hide if expiry is disabled
    }),
    QueryCountDashboardWidget({
      title: t`Active Build Orders`,
      modelType: ModelType.build,
      params: { outstanding: true }
    }),
    QueryCountDashboardWidget({
      title: t`Overdue Build Orders`,
      modelType: ModelType.build,
      params: { overdue: true }
    }),
    QueryCountDashboardWidget({
      title: t`Active Sales Orders`,
      modelType: ModelType.salesorder,
      params: { outstanding: true }
    }),
    QueryCountDashboardWidget({
      title: t`Overdue Sales Orders`,
      modelType: ModelType.salesorder,
      params: { overdue: true }
    }),
    QueryCountDashboardWidget({
      title: t`Active Purchase Orders`,
      modelType: ModelType.purchaseorder,
      params: { outstanding: true }
    }),
    QueryCountDashboardWidget({
      title: t`Overdue Purchase Orders`,
      modelType: ModelType.purchaseorder,
      params: { overdue: true }
    }),
    QueryCountDashboardWidget({
      title: t`Active Return Orders`,
      modelType: ModelType.returnorder,
      params: { outstanding: true }
    }),
    QueryCountDashboardWidget({
      title: t`Overdue Return Orders`,
      modelType: ModelType.returnorder,
      params: { overdue: true }
    })
  ];
}

/**
 *
 * @returns A list of built-in dashboard widgets
 */
export default function BuiltinDashboardWidgets(): DashboardWidgetProps[] {
  return [...BuiltinQueryCountWidgets()];
}
