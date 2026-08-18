import { t } from '@lingui/core/macro';

import { ncrDispositionStatusType } from '../../defaults/backendMappings';

import { ModelType } from '@lib/enums/ModelType';
import type { TableFilter } from '@lib/types/Filters';
import {
  AssignedToMeFilter,
  OrderStatusFilter,
  OverdueFilter,
  ResponsibleFilter,
  StatusFilterOptions,
  TagsFilter,
  UserFilter
} from '../../components/tables/Filter';

export default function NonConformanceFilters(): TableFilter[] {
  return [
    OrderStatusFilter({ model: ModelType.nonconformance }),
    {
      name: 'disposition',
      label: t`Disposition`,
      description: t`Filter by NCR disposition`,
      choiceFunction: StatusFilterOptions(ncrDispositionStatusType as ModelType)
    },
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
