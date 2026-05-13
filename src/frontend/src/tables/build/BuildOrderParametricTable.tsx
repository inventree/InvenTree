import { ApiEndpoints, ModelType } from '@lib/index';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { type ReactNode, useMemo } from 'react';
import { useGlobalSettingsState } from '../../states/SettingsStates';
import {
  DescriptionColumn,
  PartColumn,
  ReferenceColumn
} from '../ColumnRenderers';
import ParametricDataTable from '../general/ParametricDataTable';
import BuildOrderFilters from './BuildOrderFilters';

export default function BuildOrderParametricTable({
  queryParams
}: {
  queryParams?: Record<string, any>;
}): ReactNode {
  const globalSettings = useGlobalSettingsState();

  const customColumns: TableColumn[] = useMemo(() => {
    return [
      ReferenceColumn({
        switchable: false
      }),
      PartColumn({
        part: 'part_detail',
        title: t`Part`
      }),
      DescriptionColumn({
        accessor: 'title'
      })
    ];
  }, []);

  const customFilters: TableFilter[] = useMemo(() => {
    return BuildOrderFilters({
      includeDateFilters: true,
      externalBuilds: globalSettings.isSet('BUILDORDER_EXTERNAL_BUILDS')
    });
  }, [globalSettings]);

  return (
    <ParametricDataTable
      modelType={ModelType.build}
      endpoint={ApiEndpoints.build_order_list}
      customColumns={customColumns}
      customFilters={customFilters}
      queryParams={{
        part_detail: true,
        ...queryParams
      }}
    />
  );
}
