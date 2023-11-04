/**
 * Common rendering functions for table column data.
 */
import { t } from '@lingui/macro';

import { ModelType } from '../render/ModelType';
import { RenderOwner } from '../render/User';
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

export function ResponsibleColumn(): TableColumn {
  return {
    accessor: 'responsible',
    title: t`Responsible`,
    sortable: true,
    render: (record: any) =>
      record.responsible && RenderOwner({ instance: record.responsible_detail })
  };
}

export function TargetDateColumn(): TableColumn {
  return {
    accessor: 'target_date',
    title: t`Target Date`,
    sortable: true
    // TODO: custom renderer which alerts user if target date is overdue
  };
}

export function CreationDateColumn(): TableColumn {
  return {
    accessor: 'creation_date',
    title: t`Creation Date`,
    sortable: true
  };
}

export function ShipmentDateColumn(): TableColumn {
  return {
    accessor: 'shipment_date',
    title: t`Shipment Date`,
    sortable: true
  };
}
