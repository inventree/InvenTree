import { t } from '@lingui/macro';

import { ModelType } from '../../enums/ModelType';
import DisplayWidget from '../widgets/DisplayWidget';
import GetStartedWidget from '../widgets/GetStartedWidget';
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
      description: t`Show the number of parts which you have subscribed to`,
      modelType: ModelType.part,
      params: { starred: true }
    }),
    QueryCountDashboardWidget({
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
      description: t`Show the number of parts which are low on stock`,
      modelType: ModelType.part,
      params: { low_stock: true }
    }),
    // TODO: Required for build orders
    QueryCountDashboardWidget({
      title: t`Expired Stock Items`,
      description: t`Show the number of stock items which have expired`,
      modelType: ModelType.stockitem,
      params: { expired: true }
      // TODO: Hide if expiry is disabled
    }),
    QueryCountDashboardWidget({
      title: t`Stale Stock Items`,
      description: t`Show the number of stock items which are stale`,
      modelType: ModelType.stockitem,
      params: { stale: true }
      // TODO: Hide if expiry is disabled
    }),
    QueryCountDashboardWidget({
      title: t`Active Build Orders`,
      description: t`Show the number of build orders which are currently active`,
      modelType: ModelType.build,
      params: { outstanding: true }
    }),
    QueryCountDashboardWidget({
      title: t`Overdue Build Orders`,
      description: t`Show the number of build orders which are overdue`,
      modelType: ModelType.build,
      params: { overdue: true }
    }),
    QueryCountDashboardWidget({
      title: t`Assigned Build Orders`,
      description: t`Show the number of build orders which are assigned to you`,
      modelType: ModelType.build,
      params: { assigned_to_me: true, outstanding: true }
    }),
    QueryCountDashboardWidget({
      title: t`Active Sales Orders`,
      description: t`Show the number of sales orders which are currently active`,
      modelType: ModelType.salesorder,
      params: { outstanding: true }
    }),
    QueryCountDashboardWidget({
      title: t`Overdue Sales Orders`,
      description: t`Show the number of sales orders which are overdue`,
      modelType: ModelType.salesorder,
      params: { overdue: true }
    }),
    QueryCountDashboardWidget({
      title: t`Assigned Sales Orders`,
      description: t`Show the number of sales orders which are assigned to you`,
      modelType: ModelType.salesorder,
      params: { assigned_to_me: true, outstanding: true }
    }),
    QueryCountDashboardWidget({
      title: t`Active Purchase Orders`,
      description: t`Show the number of purchase orders which are currently active`,
      modelType: ModelType.purchaseorder,
      params: { outstanding: true }
    }),
    QueryCountDashboardWidget({
      title: t`Overdue Purchase Orders`,
      description: t`Show the number of purchase orders which are overdue`,
      modelType: ModelType.purchaseorder,
      params: { overdue: true }
    }),
    QueryCountDashboardWidget({
      title: t`Assigned Purchase Orders`,
      description: t`Show the number of purchase orders which are assigned to you`,
      modelType: ModelType.purchaseorder,
      params: { assigned_to_me: true, outstanding: true }
    }),
    QueryCountDashboardWidget({
      title: t`Active Return Orders`,
      description: t`Show the number of return orders which are currently active`,
      modelType: ModelType.returnorder,
      params: { outstanding: true }
    }),
    QueryCountDashboardWidget({
      title: t`Overdue Return Orders`,
      description: t`Show the number of return orders which are overdue`,
      modelType: ModelType.returnorder,
      params: { overdue: true }
    }),
    QueryCountDashboardWidget({
      title: t`Assigned Return Orders`,
      description: t`Show the number of return orders which are assigned to you`,
      modelType: ModelType.returnorder,
      params: { assigned_to_me: true, outstanding: true }
    })
  ];
}

export function BuiltinGettingStartedWidgets(): DashboardWidgetProps[] {
  return [
    {
      label: 'getting-started',
      title: t`Getting Started`,
      description: t`Getting started with InvenTree`,
      minWidth: 5,
      minHeight: 4,
      render: () => <GetStartedWidget />
    }
  ];
}

export function BuiltingSettinsWidgets(): DashboardWidgetProps[] {
  return [
    {
      label: 'color-settings',
      title: t`Color Settings`,
      description: t`Toggle user interface color mode`,
      minWidth: 3,
      minHeight: 2,
      render: () => <DisplayWidget />
    }
  ];
}

/**
 *
 * @returns A list of built-in dashboard widgets
 */
export function BuiltinDashboardWidgets(): DashboardWidgetProps[] {
  return [
    ...BuiltinQueryCountWidgets(),
    ...BuiltinGettingStartedWidgets(),
    ...BuiltingSettinsWidgets()
  ];
}

export default function AvailableDashboardWidgets(): DashboardWidgetProps[] {
  return [
    ...BuiltinDashboardWidgets()
    // TODO: Add plugin widgets here
  ];
}
