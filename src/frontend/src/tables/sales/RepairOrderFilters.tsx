import { ModelType } from '@lib/enums/ModelType';
import type { TableFilter } from '@lib/types/Filters';
import {
  CompletedAfterFilter,
  CompletedBeforeFilter,
  CreatedAfterFilter,
  CreatedBeforeFilter,
  HasStartDateFilter,
  HasTargetDateFilter,
  IncludeVariantsFilter,
  MaxDateFilter,
  MinDateFilter,
  OrderStatusFilter,
  OutstandingFilter,
  OverdueFilter,
  StartDateAfterFilter,
  StartDateBeforeFilter,
  TargetDateAfterFilter,
  TargetDateBeforeFilter
} from '../../components/tables/Filter';

export default function RepairOrderFilters({
  partId,
  includeDateFilters = true
}: {
  partId?: number;
  includeDateFilters?: boolean;
}): TableFilter[] {
  const filters: TableFilter[] = [
    OrderStatusFilter({ model: ModelType.repairorder }),
    OutstandingFilter(),
    OverdueFilter()
  ];

  if (!!partId) {
    filters.push(IncludeVariantsFilter());
  }

  const dateFilters: TableFilter[] = [
    MinDateFilter(),
    MaxDateFilter(),
    CreatedBeforeFilter(),
    CreatedAfterFilter(),
    HasStartDateFilter(),
    StartDateBeforeFilter(),
    StartDateAfterFilter(),
    HasTargetDateFilter(),
    TargetDateBeforeFilter(),
    TargetDateAfterFilter(),
    CompletedBeforeFilter(),
    CompletedAfterFilter()
  ];

  if (includeDateFilters) {
    filters.push(...dateFilters);
  }

  return filters;
}
