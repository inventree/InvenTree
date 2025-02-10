import { t } from '@lingui/macro';
import { BarChart } from '@mantine/charts';
import { Group, SimpleGrid, Text } from '@mantine/core';
import { type ReactNode, useCallback, useMemo } from 'react';

import { formatCurrency, formatDate } from '../../../defaults/formatters';
import { ApiEndpoints } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import type { TableColumn } from '../../../tables/Column';
import { InvenTreeTable } from '../../../tables/InvenTreeTable';
import { NoPricingData } from './PricingPanel';

export default function PurchaseHistoryPanel({
  part
}: Readonly<{
  part: any;
}>): ReactNode {
  const table = useTable('pricingpurchasehistory');

  const calculateUnitPrice = useCallback((record: any) => {
    const pack_quantity =
      record?.supplier_part_detail?.pack_quantity_native ?? 1;
    const unit_price = record.purchase_price / pack_quantity;

    return unit_price;
  }, []);

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'order',
        title: t`Purchase Order`,
        render: (record: any) => record?.order_detail?.reference,
        sortable: true,
        switchable: false
      },
      {
        accessor: 'order_detail.complete_date',
        ordering: 'complete_date',
        title: t`Date`,
        sortable: true,
        switchable: true,
        render: (record: any) => formatDate(record.order_detail.complete_date)
      },
      {
        accessor: 'purchase_price',
        title: t`Purchase Price`,
        sortable: true,
        switchable: false,
        render: (record: any) => {
          const price = formatCurrency(record.purchase_price, {
            currency: record.purchase_price_currency
          });

          const packQuatity = record.supplier_part_detail?.pack_quantity;
          const hasPackQuantity =
            !!packQuatity &&
            record.supplier_part_detail?.pack_quantity_native != 1;

          return (
            <Group justify='space-between' gap='xs'>
              <Text>{price}</Text>
              {hasPackQuantity && <Text size='xs'>[{packQuatity}]</Text>}
            </Group>
          );
        }
      },
      {
        accessor: 'unit_price',
        title: t`Unit Price`,
        ordering: 'purchase_price',
        sortable: true,
        switchable: false,
        render: (record: any) => {
          const price = formatCurrency(calculateUnitPrice(record), {
            currency: record.purchase_price_currency
          });

          const units = record.part_detail?.units;
          const hasUnits = !!units && units !== 1;

          return (
            <Group justify='space-between' gap='xs'>
              <Text>{price}</Text>
              {hasUnits && <Text size='xs'>[{units}]</Text>}
            </Group>
          );
        }
      }
    ];
  }, []);

  const purchaseHistoryData = useMemo(() => {
    return table.records.map((record: any) => {
      return {
        quantity: record.quantity,
        purchase_price: record.purchase_price,
        unit_price: calculateUnitPrice(record),
        name: record.order_detail.reference
      };
    });
  }, [table.records]);

  return (
    <SimpleGrid cols={{ base: 1, md: 2 }}>
      <InvenTreeTable
        tableState={table}
        url={apiUrl(ApiEndpoints.purchase_order_line_list)}
        columns={columns}
        props={{
          params: {
            base_part: part.pk,
            part_detail: true,
            order_detail: true,
            has_pricing: true,
            order_complete: true
          }
        }}
      />
      {purchaseHistoryData.length > 0 ? (
        <BarChart
          data={purchaseHistoryData}
          dataKey='name'
          series={[
            { name: 'unit_price', label: t`Unit Price`, color: 'blue.5' }
          ]}
        />
      ) : (
        <NoPricingData />
      )}
    </SimpleGrid>
  );
}
