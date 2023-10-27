import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { Thumbnail } from '../../images/Thumbnail';
import { ModelType } from '../../render/ModelType';
import { StatusRenderer } from '../../renderers/StatusRenderer';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * Display a table of purchase orders
 */
export function PurchaseOrderTable({ params }: { params?: any }) {
  const navigate = useNavigate();

  const { tableKey } = useTableRefresh('purchase-order');

  // TODO: Custom filters

  // TODO: Row actions

  // TODO: Table actions (e.g. create new purchase order)

  const tableColumns = useMemo(() => {
    return [
      {
        accessor: 'reference',
        title: t`Reference`,
        sortable: true,
        switchable: false
      },
      {
        accessor: 'description',
        title: t`Description`,
        switchable: true
      },
      {
        accessor: 'supplier__name',
        title: t`Supplier`,
        sortable: true,
        render: function (record: any) {
          let supplier = record.supplier_detail ?? {};

          return (
            <Group spacing="xs" noWrap={true}>
              <Thumbnail src={supplier?.image} alt={supplier.name} />
              <Text>{supplier?.name}</Text>
            </Group>
          );
        }
      },
      {
        accessor: 'supplier_reference',
        title: t`Supplier Reference`,
        switchable: true
      },
      {
        accessor: 'project_code',
        title: t`Project Code`,
        switchable: true
        // TODO: Custom formatter
      },
      {
        accessor: 'status',
        title: t`Status`,
        sortable: true,
        switchable: true,
        render: (record: any) =>
          StatusRenderer({
            status: record.status,
            type: ModelType.purchaseorder
          })
      },
      {
        accessor: 'creation_date',
        title: t`Created`,
        switchable: true
        // TODO: Custom formatter
      },
      {
        accessor: 'target_date',
        title: t`Target Date`,
        switchable: true
        // TODO: Custom formatter
      },
      {
        accessor: 'line_items',
        title: t`Line Items`,
        sortable: true,
        switchable: true
      }
      // TODO: total_price
      // TODO: responsible
    ];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.purchase_order_list)}
      tableKey={tableKey}
      columns={tableColumns}
      props={{
        params: {
          ...params,
          supplier_detail: true
        },
        onRowClick: (row: any) => {
          if (row.pk) {
            navigate(`/purchasing/purchase-order/${row.pk}`);
          }
        }
      }}
    />
  );
}
