/**
 * Common rendering functions for table column data.
 */
import { t } from '@lingui/macro';

import { ModelType } from '../render/ModelType';
import { TableStatusRenderer } from '../renderers/StatusRenderer';
import { TableColumn } from './Column';
import { ProjectCodeHoverCard } from './TableHoverCard';

export function DescriptionColumn(): TableColumn {
  return {
    accessor: 'description',
    title: t`Description`,
    sortable: false,
    switchable: true
  };
}

export function ProjectCodeColumn(): TableColumn {
  return {
    accessor: 'project_code',
    title: t`Project Code`,
    sortable: true,
    render: (record: any) => (
      <ProjectCodeHoverCard projectCode={record.project_code_detail} />
    )
  };
}

export function StatusColumn(model: ModelType) {
  return {
    accessor: 'status',
    sortable: true,
    title: t`Status`,
    render: TableStatusRenderer(model)
  };
}
