/**
 * Common rendering functions for table column data.
 */
import { t } from '@lingui/macro';

import { TableColumn } from './Column';
import { ProjectCodeHoverCard } from './TableHoverCard';

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
