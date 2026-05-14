import { ModelType } from '@lib/enums/ModelType';
import type { TableFilter } from '@lib/types/Filters';
import {
  AssignedToMeFilter,
  CompletedAfterFilter,
  CompletedBeforeFilter,
  CreatedAfterFilter,
  CreatedBeforeFilter,
  CreatedByFilter,
  HasProjectCodeFilter,
  HasStartDateFilter,
  HasTargetDateFilter,
  IncludeVariantsFilter,
  MaxDateFilter,
  MinDateFilter,
  OrderStatusFilter,
  OutstandingFilter,
  OverdueFilter,
  ProjectCodeFilter,
  ResponsibleFilter,
  StartDateAfterFilter,
  StartDateBeforeFilter,
  TargetDateAfterFilter,
  TargetDateBeforeFilter,
  UpdatedAfterFilter,
  UpdatedBeforeFilter
} from '../Filter';

export default function SalesOrderFilters({
  partId,
  includeDateFilters = true
}: {
  partId?: number;
  includeDateFilters?: boolean;
}): TableFilter[] {
  const filters: TableFilter[] = [
    OrderStatusFilter({ model: ModelType.salesorder }),
    OutstandingFilter(),
    OverdueFilter(),
    AssignedToMeFilter(),
    HasProjectCodeFilter(),
    ProjectCodeFilter(),
    ResponsibleFilter(),
    CreatedByFilter()
  ];

  const dateFilters: TableFilter[] = [
    MinDateFilter(),
    MaxDateFilter(),
    CreatedBeforeFilter(),
    CreatedAfterFilter(),
    TargetDateBeforeFilter(),
    TargetDateAfterFilter(),
    StartDateBeforeFilter(),
    StartDateAfterFilter(),
    HasTargetDateFilter(),
    HasStartDateFilter(),
    CompletedBeforeFilter(),
    CompletedAfterFilter(),
    UpdatedBeforeFilter(),
    UpdatedAfterFilter()
  ];

  if (includeDateFilters) {
    filters.push(...dateFilters);
  }

  if (!!partId) {
    filters.push(IncludeVariantsFilter());
  }

  return filters;
}
