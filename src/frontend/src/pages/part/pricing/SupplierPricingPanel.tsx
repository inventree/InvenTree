import { t } from '@lingui/macro';
import { Group, SimpleGrid, Text } from '@mantine/core';
import { useCallback, useMemo } from 'react';
import {
  Bar,
  BarChart,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

import { Thumbnail } from '../../../components/images/Thumbnail';
import { formatCurrency } from '../../../defaults/formatters';
import { ApiEndpoints } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { TableColumn } from '../../../tables/Column';
import { InvenTreeTable } from '../../../tables/InvenTreeTable';

export default function SupplierPricingPanel({ part }: { part: any }) {
  const table = useTable('pricing-supplier');

  const calculateUnitPrice = useCallback((record: any) => {
    let pack_quantity = record?.part_detail?.pack_quantity_native ?? 1;
    let unit_price = record.price / pack_quantity;

    return unit_price;
  }, []);

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'supplier',
        title: t`Supplier`,
        sortable: true,
        switchable: true,
        render: (record: any) => {
          return (
            <Group spacing="xs" noWrap>
              <Thumbnail
                src={
                  record?.supplier_detail?.thumbnail ??
                  record?.supplier_detail?.image
                }
                alt={record?.supplier_detail?.name}
                size={24}
              />
              <Text>{record.supplier_detail?.name}</Text>
            </Group>
          );
        }
      },
      {
        accessor: 'part_detail.SKU',
        title: t`SKU`,
        ordering: 'SKU',
        sortable: true,
        switchable: false
      },
      {
        accessor: 'quantity',
        title: t`Quantity`,
        sortable: true,
        switchable: false
      },
      {
        accessor: 'price',
        title: t`Supplier Price`,
        render: (record: any) =>
          formatCurrency(record.price, { currency: record.price_currency }),
        sortable: true,
        switchable: false
      },
      {
        accessor: 'unit_price',
        ordering: 'price',
        title: t`Unit Price`,
        sortable: true,
        switchable: true,
        render: (record: any) => {
          let units = record.part_detail?.pack_quantity;

          let price = formatCurrency(calculateUnitPrice(record), {
            currency: record.price_currency
          });

          return (
            <Group position="apart" spacing="xs" grow>
              <Text>{price}</Text>
              {units && <Text size="xs">[{units}]</Text>}
            </Group>
          );
        }
      }
    ];
  }, []);

  const supplierPricingData = useMemo(() => {
    return table.records.map((record: any) => {
      return {
        quantity: record.quantity,
        supplier_price: record.price,
        unit_price: calculateUnitPrice(record),
        name: record.part_detail?.SKU
      };
    });
  }, [table.records]);

  return (
    <SimpleGrid cols={2}>
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.supplier_part_pricing_list)}
        columns={columns}
        tableState={table}
        props={{
          params: {
            base_part: part.pk,
            supplier_detail: true,
            part_detail: true
          }
        }}
      />
      <ResponsiveContainer width="100%" height={500}>
        <BarChart data={supplierPricingData}>
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="unit_price" fill="#8884d8" label={t`Unit Price`} />
          <Bar
            dataKey="supplier_price"
            fill="#82ca9d"
            label={t`Supplier Price`}
          />
        </BarChart>
      </ResponsiveContainer>
    </SimpleGrid>
  );
}
