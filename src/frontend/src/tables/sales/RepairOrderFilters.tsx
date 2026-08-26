import { ModelType } from '@lib/enums/ModelType';
import type { TableFilter } from '@lib/types/Filters';
import {
  CreatedAfterFilter,
  CreatedBeforeFilter,
  MaxDateFilter,
  MinDateFilter,
  OrderStatusFilter,
  OutstandingFilter,
  OverdueFilter
} from '../../components/tables/Filter';

export default function RepairOrderFilters({
  includeDateFilters = true
}: {
  includeDateFilters?: boolean;
}): TableFilter[] {
  const filters: TableFilter[] = [
    OrderStatusFilter({ model: ModelType.repairorder }),
    OutstandingFilter(),
    OverdueFilter()
  ];

  const dateFilters: TableFilter[] = [
    MinDateFilter(),
    MaxDateFilter(),
    CreatedBeforeFilter(),
    CreatedAfterFilter()
  ];

  if (includeDateFilters) {
    filters.push(...dateFilters);
  }

  return filters;
}
