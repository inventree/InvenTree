import { t } from '@lingui/macro';
import { Text } from '@mantine/core';
import { useMemo } from 'react';

import { formatCurrency } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { DateColumn, ReferenceColumn, StatusColumn } from '../ColumnRenderers';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { TableHoverCard } from '../TableHoverCard';

export default function PartPurchaseOrdersTable({
  partId
}: {
  partId: number;
}) {
  const table = useTable('partpurchaseorders');
  const user = useUserState();

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      ReferenceColumn({
        accessor: 'order_detail.reference',
        sortable: true,
        switchable: false,
        title: t`Purchase Order`
      }),
      StatusColumn({
        accessor: 'order_detail.status',
        sortable: true,
        title: t`Status`,
        model: ModelType.purchaseorder
      }),
      {
        accessor: 'order_detail.supplier_name',
        title: t`Supplier`,
        sortable: false,
        switchable: true
      },
      {
        accessor: 'supplier_part_detail.SKU',
        ordering: 'sku',
        title: t`Supplier Part`,
        sortable: true
      },
      {
        accessor: 'supplier_part_detail.manufacturer_part_detail.MPN',
        ordering: 'mpn',
        title: t`Manufacturer Part`,
        sortable: true
      },
      {
        accessor: 'quantity',
        render: (record: any) => {
          let supplier_part = record?.supplier_part_detail ?? {};
          let part = record?.part_detail ?? supplier_part?.part_detail ?? {};
          let extra = [];

          if (supplier_part.pack_quantity_native != 1) {
            let total = record.quantity * supplier_part.pack_quantity_native;

            extra.push(
              <Text key="pack-quantity">
                {t`Pack Quantity`}: {supplier_part.pack_quantity}
              </Text>
            );

            extra.push(
              <Text key="total-quantity">
                {t`Total Quantity`}: {total} {part?.units}
              </Text>
            );
          }

          return (
            <TableHoverCard
              value={record.quantity}
              extra={extra}
              title={t`Quantity`}
            />
          );
        }
      },
      DateColumn({
        accessor: 'target_date',
        title: t`Target Date`
      }),
      {
        accessor: 'received'
      },
      {
        accessor: 'purchase_price',
        render: (record: any) =>
          formatCurrency(record.purchase_price, {
            currency: record.purchase_price_currency
          })
      }
    ];
  }, []);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [];
  }, []);

  return (
    <>
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.purchase_order_line_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            base_part: partId,
            part_detail: true,
            order_detail: true,
            supplier_detail: true
          },
          modelField: 'order',
          modelType: ModelType.purchaseorder
        }}
      />
    </>
  );
}
