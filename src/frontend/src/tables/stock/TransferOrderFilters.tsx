import { ModelType, type TableFilter } from '@lib/index';
import { t } from '@lingui/core/macro';
import {
  AssignedToMeFilter,
  CompletedAfterFilter,
  CompletedBeforeFilter,
  CreatedAfterFilter,
  CreatedBeforeFilter,
  CreatedByFilter,
  HasProjectCodeFilter,
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
  TagsFilter,
  TargetDateAfterFilter,
  TargetDateBeforeFilter
} from '../../components/tables/Filter';

export default function TransferOrderFilters({
  partId,
  includeDateFilters = true
}: {
  partId?: number;
  includeDateFilters?: boolean;
}): TableFilter[] {
  const filters: TableFilter[] = [
    OrderStatusFilter({ model: ModelType.transferorder }),
    OutstandingFilter(),
    OverdueFilter(),
    AssignedToMeFilter(),
    HasProjectCodeFilter(),
    ProjectCodeFilter(),
    ResponsibleFilter(),
    CreatedByFilter(),
    TagsFilter({ modelType: ModelType.transferorder })
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
    CompletedAfterFilter()
  ];

  if (includeDateFilters) {
    filters.push(...dateFilters);
  }

  if (!!partId) {
    filters.push(IncludeVariantsFilter());
  }

  return filters;
}
