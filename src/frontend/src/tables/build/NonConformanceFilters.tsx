import { t } from '@lingui/core/macro';

import { ModelType } from '@lib/enums/ModelType';
import type { TableFilter } from '@lib/types/Filters';
import {
  AssignedToMeFilter,
  OrderStatusFilter,
  OverdueFilter,
  ResponsibleFilter,
  TagsFilter,
  UserFilter
} from '../../components/tables/Filter';

export default function NonConformanceFilters(): TableFilter[] {
  return [
    OrderStatusFilter({ model: ModelType.nonconformance }),
    {
      name: 'active',
      label: t`Active`,
      type: 'boolean',
      description: t`Show NCRs which are still open`
    },
    OverdueFilter(),
    AssignedToMeFilter(),
    ResponsibleFilter(),
    UserFilter({
      name: 'raised_by',
      label: t`Raised By`,
      description: t`Filter by user who raised this report`
    }),
    TagsFilter({ modelType: ModelType.nonconformance })
  ];
}
