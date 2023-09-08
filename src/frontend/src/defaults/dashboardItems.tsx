import { t } from '@lingui/macro';

export const dashboardItems = [
  {
    id: 'starred-parts',
    text: t`Subscribed Parts`,
    icon: 'fa-bell',
    url: 'part',
    params: { starred: true }
  },
  {
    id: 'starred-categories',
    text: t`Subscribed Categories`,
    icon: 'fa-bell',
    url: 'part/category',
    params: { starred: true }
  },
  {
    id: 'latest-parts',
    text: t`Latest Parts`,
    icon: 'fa-newspaper',
    url: 'part',
    params: { ordering: '-creation_date', limit: 10 }
  },
  {
    id: 'bom-validation',
    text: t`BOM Waiting Validation`,
    icon: 'fa-times-circle',
    url: 'part',
    params: { bom_valid: false }
  },
  {
    id: 'recently-updated-stock',
    text: t`Recently Updated`,
    icon: 'fa-clock',
    url: 'stock',
    params: { part_detail: true, ordering: '-updated', limit: 10 }
  },
  {
    id: 'low-stock',
    text: t`Low Stock`,
    icon: 'fa-flag',
    url: 'part',
    params: { low_stock: true }
  },
  {
    id: 'depleted-stock',
    text: t`Depleted Stock`,
    icon: 'fa-times',
    url: 'part',
    params: { depleted_stock: true }
  },
  {
    id: 'stock-to-build',
    text: t`Required for Build Orders`,
    icon: 'fa-bullhorn',
    url: 'part',
    params: { stock_to_build: true }
  },
  {
    id: 'expired-stock',
    text: t`Expired Stock`,
    icon: 'fa-calendar-times',
    url: 'stock',
    params: { expired: true }
  },
  {
    id: 'stale-stock',
    text: t`Stale Stock`,
    icon: 'fa-stopwatch',
    url: 'stock',
    params: { stale: true, expired: true }
  },
  {
    id: 'build-pending',
    text: t`Build Orders In Progress`,
    icon: 'fa-cogs',
    url: 'build',
    params: { active: true }
  },
  {
    id: 'build-overdue',
    text: t`Overdue Build Orders`,
    icon: 'fa-calendar-times',
    url: 'build',
    params: { overdue: true }
  },
  {
    id: 'po-outstanding',
    text: t`Outstanding Purchase Orders`,
    icon: 'fa-sign-in-alt',
    url: 'order/po',
    params: { supplier_detail: true, outstanding: true }
  },
  {
    id: 'po-overdue',
    text: t`Overdue Purchase Orders`,
    icon: 'fa-calendar-times',
    url: 'order/po',
    params: { supplier_detail: true, overdue: true }
  },
  {
    id: 'so-outstanding',
    text: t`Outstanding Sales Orders`,
    icon: 'fa-sign-out-alt',
    url: 'order/so',
    params: { customer_detail: true, outstanding: true }
  },
  {
    id: 'so-overdue',
    text: t`Overdue Sales Orders`,
    icon: 'fa-calendar-times',
    url: 'order/so',
    params: { customer_detail: true, overdue: true }
  },
  {
    id: 'news',
    text: t`Current News`,
    icon: 'fa-newspaper',
    url: 'news',
    params: {}
  }
];
