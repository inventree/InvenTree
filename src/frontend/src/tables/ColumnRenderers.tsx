/**
 * Common rendering functions for table column data.
 */
import { t } from '@lingui/core/macro';
import { Anchor, Center, Group, Skeleton, Text, Tooltip } from '@mantine/core';
import {
  IconBell,
  IconExclamationCircle,
  IconLink,
  IconLock
} from '@tabler/icons-react';

import { ProgressBar } from '@lib/components/ProgressBar';
import { YesNoButton } from '@lib/components/YesNoButton';
import type { ModelType } from '@lib/enums/ModelType';
import { resolveItem } from '@lib/functions/Conversion';
import { cancelEvent } from '@lib/functions/Events';
import type { TableColumn, TableColumnProps } from '@lib/types/Tables';
import { Thumbnail } from '../components/images/Thumbnail';
import { TableStatusRenderer } from '../components/render/StatusRenderer';
import { RenderOwner, RenderUser } from '../components/render/User';
import {
  formatCurrency,
  formatDate,
  formatDecimal
} from '../defaults/formatters';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../states/SettingsStates';
import { ProjectCodeHoverCard, TableHoverCard } from './TableHoverCard';

export type PartColumnProps = TableColumnProps & {
  part?: string;
  full_name?: boolean;
};

// Extract rendering function for Part column
export function RenderPartColumn({
  part,
  full_name
}: {
  part: any;
  full_name?: boolean;
}) {
  if (!part) {
    return <Skeleton />;
  }

  return (
    <Group justify='space-between' wrap='nowrap'>
      <Thumbnail
        src={part?.thumbnail ?? part?.image}
        text={full_name ? part?.full_name : part?.name}
        hover
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
  );
}

// Render a Part instance within a table
export function PartColumn(props: PartColumnProps): TableColumn {
  return {
    accessor: 'part',
    title: t`Part`,
    sortable: true,
    switchable: false,
    minWidth: '175px',
    render: (record: any) => {
      const part =
        props.part === ''
          ? record
          : resolveItem(record, props.part ?? props.accessor ?? 'part_detail');

      return RenderPartColumn({
        part: part,
        full_name: props.full_name ?? false
      });
    },
    ...props
  };
}

export function CompanyColumn({
  company
}: {
  company: any;
}) {
  return company ? (
    <Group gap='xs' wrap='nowrap'>
      <Thumbnail
        src={company.thumbnail ?? company.image ?? ''}
        alt={company.name}
        size={24}
        hover
      />
      <Text>{company.name}</Text>
    </Group>
  ) : (
    <Skeleton />
  );
}

/**
 * Return a column which displays a tree path for a given record.
 */
export function PathColumn(props: TableColumnProps): TableColumn {
  return {
    ...props,
    accessor: props.accessor ?? 'path',
    render: (record: any) => {
      const instance = resolveItem(record, props.accessor ?? '');

      if (!instance || !instance.name) {
        return '-';
      }

      const name = instance.name ?? '';
      const pathstring = instance.pathstring || name;

      if (name == pathstring) {
        return <Text>{name}</Text>;
      }

      return (
        <TableHoverCard
          value={<Text>{instance.name}</Text>}
          icon='sitemap'
          title={props.title}
          extra={[<Text>{instance.pathstring}</Text>]}
        />
      );
    }
  };
}

export function PathColumnPlainText(props: TableColumnProps): TableColumn {
  return {
    ...props,
    accessor: props.accessor ?? 'path',
    render: (record: any) => {
      const instance = resolveItem(record, props.accessor ?? '');

      if (!instance || !instance.pathstring) {
        return '-';
      }

      return <Text>{instance.pathstring}</Text>;
    }
  };
}

export function LocationColumn(props: TableColumnProps): TableColumn {
  const userSettings = useUserSettingsState.getState();
  const enabled = userSettings.isSet('SHOW_FULL_LOCATION_IN_TABLES', false);
  if (enabled) {
    return PathColumnPlainText({
      accessor: 'location',
      title: t`Location`,
      sortable: true,
      ordering: 'location',
      minWidth: '150px',
      ...props
    });
  } else {
    return PathColumn({
      accessor: 'location',
      title: t`Location`,
      sortable: true,
      ordering: 'location',
      minWidth: '125px',
      ...props
    });
  }
}

export function DefaultLocationColumn(props: TableColumnProps): TableColumn {
  const userSettings = useUserSettingsState.getState();
  const enabled = userSettings.isSet('SHOW_FULL_LOCATION_IN_TABLES', false);
  if (enabled) {
    return PathColumnPlainText({
      accessor: 'default_location',
      title: t`Default Location`,
      sortable: true,
      defaultVisible: false,
      ordering: 'default_location',
      ...props
    });
  } else {
    return PathColumn({
      accessor: 'default_location',
      title: t`Default Location`,
      sortable: true,
      defaultVisible: false,
      ordering: 'default_location',
      ...props
    });
  }
}

export function CategoryColumn(props: TableColumnProps): TableColumn {
  const userSettings = useUserSettingsState.getState();
  const enabled = userSettings.isSet('SHOW_FULL_CATEGORY_IN_TABLES', false);
  if (enabled) {
    return PathColumnPlainText({
      accessor: 'category',
      title: t`Category`,
      sortable: true,
      ordering: 'category',
      minWidth: '150px',
      ...props
    });
  } else {
    return PathColumn({
      accessor: 'category',
      title: t`Category`,
      sortable: true,
      ordering: 'category',
      minWidth: '125px',
      ...props
    });
  }
}

export function BooleanColumn(props: TableColumn): TableColumn {
  return {
    sortable: true,
    switchable: true,
    minWidth: '75px',
    render: (record: any) => (
      <Center>
        <YesNoButton value={resolveItem(record, props.accessor ?? '')} />
      </Center>
    ),
    ...props
  };
}

export function DecimalColumn(props: TableColumn): TableColumn {
  return {
    render: (record: any) => {
      const value = resolveItem(record, props.accessor ?? '');
      return formatDecimal(value);
    },
    ...props
  };
}

export function DescriptionColumn(props: TableColumnProps): TableColumn {
  return {
    accessor: 'description',
    title: t`Description`,
    sortable: false,
    switchable: true,
    minWidth: '200px',
    ...props
  };
}

export function LinkColumn(props: TableColumnProps): TableColumn {
  return {
    accessor: 'link',
    sortable: false,
    defaultVisible: false,
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
          title={url}
        >
          <IconLink size={18} />
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

export function LineItemsProgressColumn(props: TableColumnProps): TableColumn {
  return {
    accessor: 'line_items',
    sortable: true,
    minWidth: 125,
    render: (record: any) => (
      <ProgressBar
        progressLabel={true}
        value={record.completed_lines}
        maximum={record.line_items}
      />
    ),
    ...props
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

export type StatusColumnProps = TableColumnProps & {
  model: ModelType;
};

export function StatusColumn(props: StatusColumnProps): TableColumn {
  const accessor: string = props.accessor ?? 'status';

  return {
    accessor: 'status',
    sortable: true,
    switchable: true,
    minWidth: '50px',
    render: TableStatusRenderer(props.model, accessor ?? 'status_custom_key'),
    ...props
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
      formatDate(resolveItem(record, props.accessor ?? 'date'), {
        showTime: props.extra?.showTime
      }),
    ...props
  };
}

export function StartDateColumn(props: TableColumnProps): TableColumn {
  return DateColumn({
    accessor: 'start_date',
    title: t`Start Date`,
    ...props
  });
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
