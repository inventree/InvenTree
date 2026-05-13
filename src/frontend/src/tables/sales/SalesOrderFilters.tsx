import { ModelType } from '@lib/enums/ModelType';
import type { TableFilter } from '@lib/types/Filters';
import { t } from '@lingui/core/macro';
import {
  AssignedToMeFilter,
  CompletedAfterFilter,
  CompletedBeforeFilter,
  CreatedAfterFilter,
  CreatedBeforeFilter,
  CreatedByFilter,
  HasProjectCodeFilter,
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
  includeDateFilters = true
}: {
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
    {
      name: 'has_target_date',
      type: 'boolean',
      label: t`Has Target Date`,
      description: t`Show orders with a target date`
    },
    {
      name: 'has_start_date',
      type: 'boolean',
      label: t`Has Start Date`,
      description: t`Show orders with a start date`
    },
    CompletedBeforeFilter(),
    CompletedAfterFilter(),
    UpdatedBeforeFilter(),
    UpdatedAfterFilter()
  ];

  if (includeDateFilters) {
    filters.push(...dateFilters);
  }

  return filters;
}
