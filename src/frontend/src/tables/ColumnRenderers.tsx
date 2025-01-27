/**
 * Common rendering functions for table column data.
 */
import { t } from '@lingui/macro';
import { Anchor, Group, Skeleton, Text, Tooltip } from '@mantine/core';
import { IconBell, IconExclamationCircle, IconLock } from '@tabler/icons-react';

import { YesNoButton } from '../components/buttons/YesNoButton';
import { Thumbnail } from '../components/images/Thumbnail';
import { ProgressBar } from '../components/items/ProgressBar';
import { TableStatusRenderer } from '../components/render/StatusRenderer';
import { RenderOwner, RenderUser } from '../components/render/User';
import { formatCurrency, formatDate } from '../defaults/formatters';
import type { ModelType } from '../enums/ModelType';
import { resolveItem } from '../functions/conversion';
import { cancelEvent } from '../functions/events';
import { useGlobalSettingsState } from '../states/SettingsState';
import type { TableColumn, TableColumnProps } from './Column';
import { ProjectCodeHoverCard } from './TableHoverCard';

// Render a Part instance within a table
export function PartColumn({
  part,
  full_name
}: {
  part: any;
  full_name?: boolean;
}) {
  return part ? (
    <Group justify='space-between' wrap='nowrap'>
      <Thumbnail
        src={part?.thumbnail ?? part?.image}
        text={full_name ? part?.full_name : part?.name}
      />
      <Group justify='flex-end' wrap='nowrap' gap='xs'>
        {part?.active == false && (
          <Tooltip label={t`Part is not active`}>
            <IconExclamationCircle color='red' size={16} />
          </Tooltip>
        )}
        {part?.locked && (
          <Tooltip label={t`Part is Locked`}>
            <IconLock size={16} />
          </Tooltip>
        )}
        {part?.starred && (
          <Tooltip label={t`You are subscribed to notifications for this part`}>
            <IconBell size={16} color='green' />
          </Tooltip>
        )}
      </Group>
    </Group>
  ) : (
    <Skeleton />
  );
}

export function LocationColumn(props: TableColumnProps): TableColumn {
  return {
    accessor: 'location',
    title: t`Location`,
    sortable: true,
    ordering: 'location',
    render: (record: any) => {
      const location = resolveItem(record, props.accessor ?? '');

      if (!location) {
        return (
          <Text style={{ fontStyle: 'italic' }}>{t`No location set`}</Text>
        );
      }

      return <Text>{location.name}</Text>;
    },
    ...props
  };
}

export function BooleanColumn(props: TableColumn): TableColumn {
  return {
    sortable: true,
    switchable: true,
    render: (record: any) => (
      <YesNoButton value={resolveItem(record, props.accessor ?? '')} />
    ),
    ...props
  };
}

export function DescriptionColumn(props: TableColumnProps): TableColumn {
  return {
    accessor: 'description',
    title: t`Description`,
    sortable: false,
    switchable: true,
    ...props
  };
}

export function LinkColumn(props: TableColumnProps): TableColumn {
  return {
    accessor: 'link',
    sortable: false,
    render: (record: any) => {
      const url = resolveItem(record, props.accessor ?? 'link');

      if (!url) {
        return '-';
      }

      return (
        <Anchor
          href={url}
          target='_blank'
          rel='noreferrer noopener'
          onClick={(event: any) => {
            cancelEvent(event);

            window.open(url, '_blank', 'noopener,noreferrer');
          }}
        >
          {url}
        </Anchor>
      );
    },
    ...props
  };
}

export function ReferenceColumn(props: TableColumnProps): TableColumn {
  return {
    accessor: 'reference',
    title: t`Reference`,
    sortable: true,
    switchable: true,
    ...props
  };
}

export function NoteColumn(props: TableColumnProps): TableColumn {
  return {
    accessor: 'note',
    sortable: false,
    title: t`Note`,
    render: (record: any) => record.note ?? record.notes,
    ...props
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

export function ProjectCodeColumn(props: TableColumnProps): TableColumn {
  const globalSettings = useGlobalSettingsState.getState();
  const enabled = globalSettings.isSet('PROJECT_CODES_ENABLED', true);

  return {
    accessor: 'project_code',
    ordering: 'project_code',
    sortable: true,
    title: t`Project Code`,
    hidden: !enabled,
    render: (record: any) => {
      const project_code = resolveItem(
        record,
        props.accessor ?? 'project_code_detail'
      );
      return <ProjectCodeHoverCard projectCode={project_code} />;
    },
    ...props
  };
}

export function StatusColumn({
  model,
  sortable,
  ordering,
  accessor,
  title,
  hidden
}: {
  model: ModelType;
  sortable?: boolean;
  accessor?: string;
  ordering?: string;
  hidden?: boolean;
  title?: string;
}) {
  return {
    accessor: accessor ?? 'status',
    sortable: sortable ?? true,
    ordering: ordering,
    title: title,
    hidden: hidden,
    render: TableStatusRenderer(model, accessor ?? 'status_custom_key')
  };
}

export function CreatedByColumn(props: TableColumnProps): TableColumn {
  return {
    accessor: 'created_by',
    title: t`Created By`,
    sortable: true,
    switchable: true,
    render: (record: any) =>
      record.created_by && RenderUser({ instance: record.created_by }),
    ...props
  };
}

export function ResponsibleColumn(props: TableColumnProps): TableColumn {
  return {
    accessor: 'responsible',
    sortable: true,
    switchable: true,
    render: (record: any) =>
      record.responsible &&
      RenderOwner({ instance: record.responsible_detail }),
    ...props
  };
}

export function DateColumn(props: TableColumnProps): TableColumn {
  return {
    accessor: 'date',
    sortable: true,
    title: t`Date`,
    switchable: true,
    render: (record: any) =>
      formatDate(resolveItem(record, props.accessor ?? 'date')),
    ...props
  };
}

export function TargetDateColumn(props: TableColumnProps): TableColumn {
  return DateColumn({
    accessor: 'target_date',
    title: t`Target Date`,
    ...props
  });
}

export function CreationDateColumn(props: TableColumnProps): TableColumn {
  return DateColumn({
    accessor: 'creation_date',
    title: t`Creation Date`,
    ...props
  });
}

export function CompletionDateColumn(props: TableColumnProps): TableColumn {
  return DateColumn({
    accessor: 'completion_date',
    title: t`Completion Date`,
    ...props
  });
}

export function ShipmentDateColumn(props: TableColumnProps): TableColumn {
  return DateColumn({
    accessor: 'shipment_date',
    title: t`Shipment Date`,
    ...props
  });
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
      const currency_key = currency_accessor ?? `${accessor}_currency`;
      return formatCurrency(resolveItem(record, accessor), {
        currency: currency ?? resolveItem(record, currency_key)
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
