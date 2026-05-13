import { ModelType } from '@lib/enums/ModelType';
import type { TableFilter } from '@lib/types/Filters';
import { t } from '@lingui/core/macro';
import {
  AssignedToMeFilter,
  CompletedAfterFilter,
  CompletedBeforeFilter,
  CreatedAfterFilter,
  CreatedBeforeFilter,
  HasProjectCodeFilter,
  HasStartDateFilter,
  HasTargetDateFilter,
  IncludeVariantsFilter,
  IssuedByFilter,
  MaxDateFilter,
  MinDateFilter,
  OrderStatusFilter,
  OutstandingFilter,
  OverdueFilter,
  PartCategoryFilter,
  ProjectCodeFilter,
  ResponsibleFilter,
  StartDateAfterFilter,
  StartDateBeforeFilter,
  TargetDateAfterFilter,
  TargetDateBeforeFilter
} from '../Filter';

/**
 * Generate a set of common filters for the build order views
 */
export default function BuildOrderFilters({
  partId,
  includeDateFilters = true,
  externalBuilds = false
}: {
  partId?: number;
  includeDateFilters: boolean;
  externalBuilds?: boolean;
}): TableFilter[] {
  const filters: TableFilter[] = [
    OutstandingFilter(),
    OrderStatusFilter({ model: ModelType.build }),
    OverdueFilter(),
    AssignedToMeFilter(),
    CompletedBeforeFilter(),
    CompletedAfterFilter(),
    ProjectCodeFilter(),
    HasProjectCodeFilter(),
    IssuedByFilter(),
    ResponsibleFilter(),
    PartCategoryFilter()
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
    HasStartDateFilter()
  ];

  // Date filters may be optionally included or excluded from the filter set
  if (includeDateFilters) {
    filters.push(...dateFilters);
  }

  if (externalBuilds) {
    filters.push({
      name: 'external',
      label: t`External`,
      description: t`Show external build orders`
    });
  }

  // If we are filtering on a specific part, we can include the "include variants" filter
  if (!!partId) {
    filters.push(IncludeVariantsFilter());
  }

  return filters;
}
