/**
 * Common rendering functions for table column data.
 */
import { t } from '@lingui/macro';
import { Anchor, Text } from '@mantine/core';

import { YesNoButton } from '../components/buttons/YesNoButton';
import { Thumbnail } from '../components/images/Thumbnail';
import { ProgressBar } from '../components/items/ProgressBar';
import { TableStatusRenderer } from '../components/render/StatusRenderer';
import { RenderOwner } from '../components/render/User';
import { formatCurrency, renderDate } from '../defaults/formatters';
import { ModelType } from '../enums/ModelType';
import { resolveItem } from '../functions/conversion';
import { cancelEvent } from '../functions/events';
import { TableColumn } from './Column';
import { ProjectCodeHoverCard } from './TableHoverCard';

// Render a Part instance within a table
export function PartColumn(part: any, full_name?: boolean) {
  return (
    <Thumbnail
      src={part?.thumbnail ?? part.image}
      text={full_name ? part.full_name : part.name}
    />
  );
}

export function LocationColumn({
  accessor,
  title,
  sortable,
  ordering
}: {
  accessor: string;
  title?: string;
  sortable?: boolean;
  ordering?: string;
}): TableColumn {
  return {
    accessor: accessor,
    title: title ?? t`Location`,
    sortable: sortable ?? true,
    ordering: ordering ?? 'location',
    render: (record: any) => {
      let location = resolveItem(record, accessor);

      if (!location) {
        return <Text italic>{t`No location set`}</Text>;
      }

      return <Text>{location.name}</Text>;
    }
  };
}

export function BooleanColumn({
  accessor,
  title,
  sortable,
  switchable,
  ordering
}: {
  accessor: string;
  title?: string;
  ordering?: string;
  sortable?: boolean;
  switchable?: boolean;
}): TableColumn {
  return {
    accessor: accessor,
    title: title,
    ordering: ordering,
    sortable: sortable ?? true,
    switchable: switchable ?? true,
    render: (record: any) => (
      <YesNoButton value={resolveItem(record, accessor)} />
    )
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

export function LinkColumn({
  accessor = 'link'
}: {
  accessor?: string;
}): TableColumn {
  return {
    accessor: accessor,
    sortable: false,
    render: (record: any) => {
      let url = resolveItem(record, accessor);

      if (!url) {
        return '-';
      }

      return (
        <Anchor
          href={url}
          target="_blank"
          rel="noreferrer noopener"
          onClick={(event: any) => {
            cancelEvent(event);

            window.open(url, '_blank', 'noopener,noreferrer');
          }}
        >
          {url}
        </Anchor>
      );
    }
  };
}

export function ReferenceColumn(): TableColumn {
  return {
    accessor: 'reference',
    sortable: true,
    switchable: false
  };
}

export function NoteColumn(): TableColumn {
  return {
    accessor: 'note',
    sortable: false,
    title: t`Note`,
    render: (record: any) => record.note ?? record.notes
  };
}

export function LineItemsProgressColumn(): TableColumn {
  return {
    accessor: 'line_items',
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
    render: TableStatusRenderer(model)
  };
}

export function ResponsibleColumn(): TableColumn {
  return {
    accessor: 'responsible',
    sortable: true,
    render: (record: any) =>
      record.responsible && RenderOwner({ instance: record.responsible_detail })
  };
}

export function DateColumn({
  accessor,
  sortable,
  switchable,
  ordering,
  title
}: {
  accessor?: string;
  ordering?: string;
  sortable?: boolean;
  switchable?: boolean;
  title?: string;
}): TableColumn {
  return {
    accessor: accessor ?? 'date',
    sortable: sortable ?? true,
    ordering: ordering,
    title: title ?? t`Date`,
    switchable: switchable,
    render: (record: any) => renderDate(resolveItem(record, accessor ?? 'date'))
  };
}

export function TargetDateColumn(): TableColumn {
  return {
    accessor: 'target_date',
    sortable: true,
    title: t`Target Date`,
    // TODO: custom renderer which alerts user if target date is overdue
    render: (record: any) => renderDate(record.target_date)
  };
}

export function CreationDateColumn(): TableColumn {
  return {
    accessor: 'creation_date',
    sortable: true,
    render: (record: any) => renderDate(record.creation_date)
  };
}

export function ShipmentDateColumn(): TableColumn {
  return {
    accessor: 'shipment_date',
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
