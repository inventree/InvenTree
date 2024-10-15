import { t } from '@lingui/macro';

import { ModelType } from '../../enums/ModelType';
import { DashboardWidgetProps } from './DashboardWidget';
import ColorToggleDashboardWidget from './widgets/ColorToggleWidget';
import GetStartedWidget from './widgets/GetStartedWidget';
import LanguageSelectDashboardWidget from './widgets/LanguageSelectWidget';
import QueryCountDashboardWidget from './widgets/QueryCountDashboardWidget';

/**
 *
 * @returns A list of built-in dashboard widgets which display the number of results for a particular query
 */
export function BuiltinQueryCountWidgets(): DashboardWidgetProps[] {
  return [
    QueryCountDashboardWidget({
      label: 'sub-prt',
      title: t`Subscribed Parts`,
      description: t`Show the number of parts which you have subscribed to`,
      modelType: ModelType.part,
      params: { starred: true }
    }),
    QueryCountDashboardWidget({
      label: 'sub-cat',
      title: t`Subscribed Categories`,
      description: t`Show the number of part categories which you have subscribed to`,
      modelType: ModelType.partcategory,
      params: { starred: true }
    }),
    // TODO: 'latest parts'
    // TODO: 'BOM waiting validation'
    // TODO: 'recently updated stock'
    QueryCountDashboardWidget({
      title: t`Low Stock`,
      label: 'low-stk',
      description: t`Show the number of parts which are low on stock`,
      modelType: ModelType.part,
      params: { low_stock: true }
    }),
    // TODO: Required for build orders
    QueryCountDashboardWidget({
      title: t`Expired Stock Items`,
      label: 'exp-stk',
      description: t`Show the number of stock items which have expired`,
      modelType: ModelType.stockitem,
      params: { expired: true }
      // TODO: Hide if expiry is disabled
    }),
    QueryCountDashboardWidget({
      title: t`Stale Stock Items`,
      label: 'stl-stk',
      description: t`Show the number of stock items which are stale`,
      modelType: ModelType.stockitem,
      params: { stale: true }
      // TODO: Hide if expiry is disabled
    }),
    QueryCountDashboardWidget({
      title: t`Active Build Orders`,
      label: 'act-bo',
      description: t`Show the number of build orders which are currently active`,
      modelType: ModelType.build,
      params: { outstanding: true }
    }),
    QueryCountDashboardWidget({
      title: t`Overdue Build Orders`,
      label: 'ovr-bo',
      description: t`Show the number of build orders which are overdue`,
      modelType: ModelType.build,
      params: { overdue: true }
    }),
    QueryCountDashboardWidget({
      title: t`Assigned Build Orders`,
      label: 'asn-bo',
      description: t`Show the number of build orders which are assigned to you`,
      modelType: ModelType.build,
      params: { assigned_to_me: true, outstanding: true }
    }),
    QueryCountDashboardWidget({
      title: t`Active Sales Orders`,
      label: 'act-so',
      description: t`Show the number of sales orders which are currently active`,
      modelType: ModelType.salesorder,
      params: { outstanding: true }
    }),
    QueryCountDashboardWidget({
      title: t`Overdue Sales Orders`,
      label: 'ovr-so',
      description: t`Show the number of sales orders which are overdue`,
      modelType: ModelType.salesorder,
      params: { overdue: true }
    }),
    QueryCountDashboardWidget({
      title: t`Assigned Sales Orders`,
      label: 'asn-so',
      description: t`Show the number of sales orders which are assigned to you`,
      modelType: ModelType.salesorder,
      params: { assigned_to_me: true, outstanding: true }
    }),
    QueryCountDashboardWidget({
      title: t`Active Purchase Orders`,
      label: 'act-po',
      description: t`Show the number of purchase orders which are currently active`,
      modelType: ModelType.purchaseorder,
      params: { outstanding: true }
    }),
    QueryCountDashboardWidget({
      title: t`Overdue Purchase Orders`,
      label: 'ovr-po',
      description: t`Show the number of purchase orders which are overdue`,
      modelType: ModelType.purchaseorder,
      params: { overdue: true }
    }),
    QueryCountDashboardWidget({
      title: t`Assigned Purchase Orders`,
      label: 'asn-po',
      description: t`Show the number of purchase orders which are assigned to you`,
      modelType: ModelType.purchaseorder,
      params: { assigned_to_me: true, outstanding: true }
    }),
    QueryCountDashboardWidget({
      title: t`Active Return Orders`,
      label: 'act-ro',
      description: t`Show the number of return orders which are currently active`,
      modelType: ModelType.returnorder,
      params: { outstanding: true }
    }),
    QueryCountDashboardWidget({
      title: t`Overdue Return Orders`,
      label: 'ovr-ro',
      description: t`Show the number of return orders which are overdue`,
      modelType: ModelType.returnorder,
      params: { overdue: true }
    }),
    QueryCountDashboardWidget({
      title: t`Assigned Return Orders`,
      label: 'asn-ro',
      description: t`Show the number of return orders which are assigned to you`,
      modelType: ModelType.returnorder,
      params: { assigned_to_me: true, outstanding: true }
    })
  ];
}

export function BuiltinGettingStartedWidgets(): DashboardWidgetProps[] {
  return [
    {
      label: 'gstart',
      title: t`Getting Started`,
      description: t`Getting started with InvenTree`,
      minWidth: 5,
      minHeight: 4,
      render: () => <GetStartedWidget />
    }
  ];
}

export function BuiltingSettinsWidgets(): DashboardWidgetProps[] {
  return [ColorToggleDashboardWidget(), LanguageSelectDashboardWidget()];
}

/**
 *
 * @returns A list of built-in dashboard widgets
 */
export default function DashboardWidgetLibrary(): DashboardWidgetProps[] {
  return [
    ...BuiltinQueryCountWidgets(),
    ...BuiltinGettingStartedWidgets(),
    ...BuiltingSettinsWidgets()
  ];
}
