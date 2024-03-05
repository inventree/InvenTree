import { t } from '@lingui/macro';

import { ApiEndpoints } from '../enums/ApiEndpoints';

interface DashboardItems {
  id: string;
  text: string;
  icon: string;
  url: ApiEndpoints;
  params: any;
}
export const dashboardItems: DashboardItems[] = [
  {
    id: 'starred-parts',
    text: t`Subscribed Parts`,
    icon: 'fa-bell',
    url: ApiEndpoints.part_list,
    params: { starred: true }
  },
  {
    id: 'starred-categories',
    text: t`Subscribed Categories`,
    icon: 'fa-bell',
    url: ApiEndpoints.category_list,
    params: { starred: true }
  },
  {
    id: 'latest-parts',
    text: t`Latest Parts`,
    icon: 'fa-newspaper',
    url: ApiEndpoints.part_list,
    params: { ordering: '-creation_date', limit: 10 }
  },
  {
    id: 'bom-validation',
    text: t`BOM Waiting Validation`,
    icon: 'fa-times-circle',
    url: ApiEndpoints.part_list,
    params: { bom_valid: false }
  },
  {
    id: 'recently-updated-stock',
    text: t`Recently Updated`,
    icon: 'fa-clock',
    url: ApiEndpoints.stock_item_list,
    params: { part_detail: true, ordering: '-updated', limit: 10 }
  },
  {
    id: 'low-stock',
    text: t`Low Stock`,
    icon: 'fa-flag',
    url: ApiEndpoints.part_list,
    params: { low_stock: true }
  },
  {
    id: 'depleted-stock',
    text: t`Depleted Stock`,
    icon: 'fa-times',
    url: ApiEndpoints.part_list,
    params: { depleted_stock: true }
  },
  {
    id: 'stock-to-build',
    text: t`Required for Build Orders`,
    icon: 'fa-bullhorn',
    url: ApiEndpoints.part_list,
    params: { stock_to_build: true }
  },
  {
    id: 'expired-stock',
    text: t`Expired Stock`,
    icon: 'fa-calendar-times',
    url: ApiEndpoints.stock_item_list,
    params: { expired: true }
  },
  {
    id: 'stale-stock',
    text: t`Stale Stock`,
    icon: 'fa-stopwatch',
    url: ApiEndpoints.stock_item_list,
    params: { stale: true, expired: true }
  },
  {
    id: 'build-pending',
    text: t`Build Orders In Progress`,
    icon: 'fa-cogs',
    url: ApiEndpoints.build_order_list,
    params: { active: true }
  },
  {
    id: 'build-overdue',
    text: t`Overdue Build Orders`,
    icon: 'fa-calendar-times',
    url: ApiEndpoints.build_order_list,
    params: { overdue: true }
  },
  {
    id: 'po-outstanding',
    text: t`Outstanding Purchase Orders`,
    icon: 'fa-sign-in-alt',
    url: ApiEndpoints.purchase_order_list,
    params: { supplier_detail: true, outstanding: true }
  },
  {
    id: 'po-overdue',
    text: t`Overdue Purchase Orders`,
    icon: 'fa-calendar-times',
    url: ApiEndpoints.purchase_order_list,
    params: { supplier_detail: true, overdue: true }
  },
  {
    id: 'so-outstanding',
    text: t`Outstanding Sales Orders`,
    icon: 'fa-sign-out-alt',
    url: ApiEndpoints.sales_order_list,
    params: { customer_detail: true, outstanding: true }
  },
  {
    id: 'so-overdue',
    text: t`Overdue Sales Orders`,
    icon: 'fa-calendar-times',
    url: ApiEndpoints.sales_order_list,
    params: { customer_detail: true, overdue: true }
  },
  {
    id: 'news',
    text: t`Current News`,
    icon: 'fa-newspaper',
    url: ApiEndpoints.news,
    params: {}
  }
];
