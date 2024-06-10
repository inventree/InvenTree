import { t } from '@lingui/macro';
import { BarChart } from '@mantine/charts';
import { Group, SimpleGrid, Text } from '@mantine/core';
import { ReactNode, useCallback, useMemo } from 'react';

import { formatCurrency, formatDate } from '../../../defaults/formatters';
import { ApiEndpoints } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { TableColumn } from '../../../tables/Column';
import { InvenTreeTable } from '../../../tables/InvenTreeTable';
import { NoPricingData } from './PricingPanel';

export default function PurchaseHistoryPanel({
  part
}: {
  part: any;
}): ReactNode {
  const table = useTable('pricing-purchase-history');

  const calculateUnitPrice = useCallback((record: any) => {
    let pack_quantity = record?.supplier_part_detail?.pack_quantity_native ?? 1;
    let unit_price = record.purchase_price / pack_quantity;

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
          let price = formatCurrency(record.purchase_price, {
            currency: record.purchase_price_currency
          });

          let units = record.supplier_part_detail?.pack_quantity;

          return (
            <Group justify="space-between" gap="xs">
              <Text>{price}</Text>
              {units && <Text size="xs">[{units}]</Text>}
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
          let price = formatCurrency(calculateUnitPrice(record), {
            currency: record.purchase_price_currency
          });

          let units = record.part_detail?.units;

          return (
            <Group justify="space-between" gap="xs">
              <Text>{price}</Text>
              {units && <Text size="xs">[{units}]</Text>}
            </Group>
          );
        }
      }
    ];
  }, []);

  const currency: string = useMemo(() => {
    if (table.records.length === 0) {
      return '';
    }
    return table.records[0].purchase_price_currency;
  }, [table.records]);

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
    <SimpleGrid cols={2}>
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
          dataKey="name"
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
