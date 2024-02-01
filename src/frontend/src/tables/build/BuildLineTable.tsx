import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import {
  IconArrowRight,
  IconShoppingCart,
  IconTool
} from '@tabler/icons-react';
import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { PartHoverCard } from '../../components/images/Thumbnail';
import { ProgressBar } from '../../components/items/ProgressBar';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { getDetailUrl } from '../../functions/urls';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { BooleanColumn } from '../ColumnRenderers';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { TableHoverCard } from '../TableHoverCard';

export default function BuildLineTable({ params = {} }: { params?: any }) {
  const table = useTable('buildline');
  const user = useUserState();
  const navigate = useNavigate();

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'allocated',
        label: t`Allocated`,
        description: t`Show allocated lines`
      },
      {
        name: 'available',
        label: t`Available`,
        description: t`Show lines with available stock`
      },
      {
        name: 'consumable',
        label: t`Consumable`,
        description: t`Show consumable lines`
      },
      {
        name: 'optional',
        label: t`Optional`,
        description: t`Show optional lines`
      }
    ];
  }, []);

  const renderAvailableColumn = useCallback((record: any) => {
    let bom_item = record?.bom_item_detail ?? {};
    let extra: any[] = [];
    let available = record?.available_stock;

    // Account for substitute stock
    if (record.available_substitute_stock > 0) {
      available += record.available_substitute_stock;
      extra.push(
        <Text key="substitite" size="sm">
          {t`Includes substitute stock`}
        </Text>
      );
    }

    // Account for variant stock
    if (bom_item.allow_variants && record.available_variant_stock > 0) {
      available += record.available_variant_stock;
      extra.push(
        <Text key="variant" size="sm">
          {t`Includes variant stock`}
        </Text>
      );
    }

    // Account for in-production stock
    if (record.in_production > 0) {
      extra.push(
        <Text key="production" size="sm">
          {t`In production`}: {record.in_production}
        </Text>
      );
    }

    // Account for stock on order
    if (record.on_order > 0) {
      extra.push(
        <Text key="on-order" size="sm">
          {t`On order`}: {record.on_order}
        </Text>
      );
    }

    return (
      <TableHoverCard
        value={
          available > 0 ? (
            available
          ) : (
            <Text color="red" italic>{t`No stock available`}</Text>
          )
        }
        title={t`Available Stock`}
        extra={extra}
      />
    );
  }, []);

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'bom_item',
        title: t`Part`,
        sortable: true,
        switchable: false,
        render: (record: any) => <PartHoverCard part={record.part_detail} />
      },
      {
        accessor: 'reference',
        title: t`Reference`,
        render: (record: any) => record.bom_item_detail.reference
      },
      BooleanColumn({
        accessor: 'bom_item_detail.consumable',
        title: t`Consumable`
      }),
      BooleanColumn({
        accessor: 'bom_item_detail.optional',
        title: t`Optional`
      }),
      {
        accessor: 'unit_quantity',
        title: t`Unit Quantity`,
        sortable: true,
        render: (record: any) => {
          return (
            <Group position="apart">
              <Text>{record.bom_item_detail?.quantity}</Text>
              {record?.part_detail?.units && (
                <Text size="xs">[{record.part_detail.units}]</Text>
              )}
            </Group>
          );
        }
      },
      {
        accessor: 'quantity',
        title: t`Required Quantity`,
        sortable: true,
        render: (record: any) => {
          return (
            <Group position="apart">
              <Text>{record.quantity}</Text>
              {record?.part_detail?.units && (
                <Text size="xs">[{record.part_detail.units}]</Text>
              )}
            </Group>
          );
        }
      },
      {
        accessor: 'available_stock',
        title: t`Available`,
        sortable: true,
        switchable: false,
        render: renderAvailableColumn
      },
      {
        accessor: 'allocated',
        title: t`Allocated`,
        switchable: false,
        render: (record: any) => {
          return record?.bom_item_detail?.consumable ? (
            <Text italic>{t`Consumable item`}</Text>
          ) : (
            <ProgressBar
              progressLabel={true}
              value={record.allocated}
              maximum={record.quantity}
            />
          );
        }
      }
    ];
  }, []);

  const rowActions = useCallback(
    (record: any) => {
      let part = record.part_detail;

      // Consumable items have no appropriate actions
      if (record?.bom_item_detail?.consumable) {
        return [];
      }

      return [
        {
          icon: <IconArrowRight />,
          title: t`Allocate Stock`,
          hidden: record.allocated >= record.quantity,
          color: 'green'
        },
        {
          icon: <IconShoppingCart />,
          title: t`Order Stock`,
          hidden: !part?.purchaseable,
          color: 'blue'
        },
        {
          icon: <IconTool />,
          title: t`Build Stock`,
          hidden: !part?.assembly,
          color: 'blue'
        }
      ];
    },
    [user]
  );

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.build_line_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        params: {
          ...params,
          part_detail: true
        },
        tableFilters: tableFilters,
        rowActions: rowActions,
        onRowClick: (row: any) => {
          if (row?.part_detail?.pk) {
            navigate(getDetailUrl(ModelType.part, row.part_detail.pk));
          }
        }
      }}
    />
  );
}
