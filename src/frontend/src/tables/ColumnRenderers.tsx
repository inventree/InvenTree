/**
 * Common rendering functions for table column data.
 */
import { t } from '@lingui/core/macro';
import {
  Anchor,
  Badge,
  Center,
  Group,
  Skeleton,
  Text,
  Tooltip
} from '@mantine/core';
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
import type { ReactNode } from 'react';
import { Thumbnail } from '../components/images/Thumbnail';
import { TableStatusRenderer } from '../components/render/StatusRenderer';
import { RenderOwner } from '../components/render/User';
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
      const part = resolveItem(
        record,
        props.part ?? props.accessor ?? 'part_detail'
      );

      return RenderPartColumn({
        part: part,
        full_name: props.full_name ?? false
      });
    },
    ...props
  };
}

export type StockColumnProps = TableColumnProps & {
  nullMessage?: string | ReactNode;
};

// Render a StockItem instance within a table
export function StockColumn(props: StockColumnProps): TableColumn {
  return {
    accessor: props.accessor ?? 'stock_item',
    title: t`Stock Item`,
    ...props,
    render: (record: any) => {
      const stock_item =
        resolveItem(record, props.accessor ?? 'stock_item_detail') ?? {};
      const part = stock_item.part_detail ?? {};

      const quantity = stock_item.quantity ?? 0;
      const allocated = stock_item.allocated ?? 0;
      const available = quantity - allocated;

      const extra: ReactNode[] = [];
      let color = undefined;
      let text = formatDecimal(quantity);

      // Handle case where stock item detail is not provided
      if (!stock_item || !stock_item.pk) {
        return props.nullMessage ?? '-';
      }

      // Override with serial number if available
      if (stock_item.serial && quantity == 1) {
        text = `# ${stock_item.serial}`;
      }

      if (record.is_building) {
        color = 'blue';
        extra.push(
          <Text
            key='production'
            size='sm'
          >{t`This stock item is in production`}</Text>
        );
      } else if (record.sales_order) {
        extra.push(
          <Text
            key='sales-order'
            size='sm'
          >{t`This stock item has been assigned to a sales order`}</Text>
        );
      } else if (record.customer) {
        extra.push(
          <Text
            key='customer'
            size='sm'
          >{t`This stock item has been assigned to a customer`}</Text>
        );
      } else if (record.belongs_to) {
        extra.push(
          <Text
            key='belongs-to'
            size='sm'
          >{t`This stock item is installed in another stock item`}</Text>
        );
      } else if (record.consumed_by) {
        extra.push(
          <Text
            key='consumed-by'
            size='sm'
          >{t`This stock item has been consumed by a build order`}</Text>
        );
      } else if (!record.in_stock) {
        extra.push(
          <Text
            key='unavailable'
            size='sm'
          >{t`This stock item is unavailable`}</Text>
        );
      }

      if (record.expired) {
        extra.push(
          <Text key='expired' size='sm'>{t`This stock item has expired`}</Text>
        );
      } else if (record.stale) {
        extra.push(
          <Text key='stale' size='sm'>{t`This stock item is stale`}</Text>
        );
      }

      if (record.in_stock) {
        if (allocated > 0) {
          if (allocated > quantity) {
            color = 'red';
            extra.push(
              <Text
                key='over-allocated'
                size='sm'
              >{t`This stock item is over-allocated`}</Text>
            );
          } else if (allocated == quantity) {
            color = 'orange';
            extra.push(
              <Text
                key='fully-allocated'
                size='sm'
              >{t`This stock item is fully allocated`}</Text>
            );
          } else {
            extra.push(
              <Text
                key='partially-allocated'
                size='sm'
              >{t`This stock item is partially allocated`}</Text>
            );
          }
        }

        if (available != quantity) {
          if (available > 0) {
            extra.push(
              <Text key='available' size='sm' c='orange'>
                {`${t`Available`}: ${formatDecimal(available)}`}
              </Text>
            );
          } else {
            extra.push(
              <Text
                key='no-stock'
                size='sm'
                c='red'
              >{t`No stock available`}</Text>
            );
          }
        }

        if (quantity <= 0) {
          extra.push(
            <Text
              key='depleted'
              size='sm'
            >{t`This stock item has been depleted`}</Text>
          );
        }
      }

      if (!record.in_stock) {
        color = 'red';
      }

      return (
        <TableHoverCard
          value={
            <Group gap='xs' justify='left' wrap='nowrap'>
              <Text c={color}>{text}</Text>
              {part.units && (
                <Text size='xs' c={color}>
                  [{part.units}]
                </Text>
              )}
            </Group>
          }
          title={t`Stock Information`}
          extra={extra}
        />
      );
    }
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

export function AllocatedLinesProgressColumn(
  props: TableColumnProps
): TableColumn {
  return {
    accessor: 'allocated_lines',
    sortable: true,
    title: t`Allocated Lines`,
    minWidth: 125,
    render: (record: any) => (
      <ProgressBar
        progressLabel={true}
        value={record.allocated_lines}
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
  const accessor: string = props.accessor ?? 'status_custom_key';

  return {
    accessor: 'status',
    sortable: true,
    switchable: true,
    minWidth: '50px',
    render: TableStatusRenderer(props.model, accessor),
    ...props
  };
}

export function UserColumn(props: TableColumnProps): TableColumn {
  return {
    accessor: 'user',
    title: t`User`,
    sortable: true,
    switchable: true,
    render: (record: any) => {
      const instance = resolveItem(record, props.accessor ?? 'user_detail');
      if (instance) {
        const extra: ReactNode[] = [
          <Text size='sm'>
            {instance.first_name} {instance.last_name}
          </Text>
        ];

        if (instance.is_active === false) {
          extra.push(
            <Badge autoContrast color='red' size='xs'>
              {t`Inactive`}
            </Badge>
          );
        }

        return (
          <TableHoverCard
            value={instance.username}
            title={t`User Information`}
            icon='user'
            extra={extra}
          />
        );
      } else {
        return '-';
      }
    },
    ...props
  };
}

export function CreatedByColumn(props: TableColumnProps): TableColumn {
  return UserColumn({
    accessor: 'created_by',
    ordering: 'created_by',
    title: t`Created By`,
    ...props
  });
}

export function OwnerColumn(props: TableColumnProps): TableColumn {
  return {
    accessor: 'owner_detail',
    ordering: 'owner',
    title: t`Owner`,
    sortable: true,
    switchable: true,
    render: (record: any) => {
      const instance = resolveItem(record, props.accessor ?? 'owner_detail');

      if (instance) {
        return <RenderOwner instance={instance} />;
      } else {
        return '-';
      }
    },
    ...props
  };
}

export function ResponsibleColumn(props: TableColumnProps): TableColumn {
  return OwnerColumn({
    accessor: 'responsible_detail',
    ordering: 'responsible',
    title: t`Responsible`,
    ...props
  });
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
