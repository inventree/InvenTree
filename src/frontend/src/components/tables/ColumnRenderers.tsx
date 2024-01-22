/**
 * Common rendering functions for table column data.
 */
import { t } from '@lingui/macro';

import { formatCurrency, renderDate } from '../../defaults/formatters';
import { ModelType } from '../../enums/ModelType';
import { Thumbnail } from '../images/Thumbnail';
import { ProgressBar } from '../items/ProgressBar';
import { YesNoButton } from '../items/YesNoButton';
import { TableStatusRenderer } from '../render/StatusRenderer';
import { RenderOwner } from '../render/User';
import { TableColumn } from './Column';
import { ProjectCodeHoverCard } from './TableHoverCard';

// Render a Part instance within a table
export function PartColumn(part: any) {
  return <Thumbnail src={part?.thumbnail ?? part.image} text={part.name} />;
}

export function BooleanColumn({
  accessor,
  title,
  sortable,
  switchable
}: {
  accessor: string;
  title: string;
  sortable?: boolean;
  switchable?: boolean;
}): TableColumn {
  return {
    accessor: accessor,
    title: title,
    sortable: sortable ?? true,
    switchable: switchable ?? true,
    render: (record: any) => <YesNoButton value={record[accessor]} />
  };
}

export function DescriptionColumn({
  accessor,
  sortable,
  switchable
}: {
  accessor?: string;
  sortable?: boolean;
  switchable?: boolean;
}): TableColumn {
  return {
    accessor: accessor ?? 'description',
    title: t`Description`,
    sortable: sortable ?? false,
    switchable: switchable ?? true
  };
}

export function LinkColumn(): TableColumn {
  return {
    accessor: 'link',
    title: t`Link`,
    sortable: false
    // TODO: Custom URL hyperlink renderer?
  };
}

export function LineItemsProgressColumn(): TableColumn {
  return {
    accessor: 'line_items',
    title: t`Line Items`,
    sortable: true,
    render: (record: any) => (
      <ProgressBar
        progressLabel={true}
        value={record.completed_lines}
        maximum={record.line_items}
      />
    )
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
    sortable: true,
    // TODO: custom renderer which alerts user if target date is overdue
    render: (record: any) => renderDate(record.target_date)
  };
}

export function CreationDateColumn(): TableColumn {
  return {
    accessor: 'creation_date',
    title: t`Creation Date`,
    sortable: true,
    render: (record: any) => renderDate(record.creation_date)
  };
}

export function ShipmentDateColumn(): TableColumn {
  return {
    accessor: 'shipment_date',
    title: t`Shipment Date`,
    sortable: true,
    render: (record: any) => renderDate(record.shipment_date)
  };
}

export function CurrencyColumn({
  accessor,
  title,
  currency,
  currency_accessor,
  sortable
}: {
  accessor: string;
  title?: string;
  currency?: string;
  currency_accessor?: string;
  sortable?: boolean;
}): TableColumn {
  return {
    accessor: accessor,
    title: title ?? t`Currency`,
    sortable: sortable ?? true,
    render: (record: any) => {
      let currency_key = currency_accessor ?? `${accessor}_currency`;
      return formatCurrency(record[accessor], {
        currency: currency ?? record[currency_key]
      });
    }
  };
}

export function TotalPriceColumn(): TableColumn {
  return CurrencyColumn({
    accessor: 'total_price',
    title: t`Total Price`
  });
}
