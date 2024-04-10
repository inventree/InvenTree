import { t } from '@lingui/macro';
import { LoadingOverlay, SimpleGrid, Stack } from '@mantine/core';
import { DataTable, DataTableColumn } from 'mantine-datatable';
import { ReactNode, useMemo } from 'react';
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';

import { formatCurrency, formatDecimal } from '../../../defaults/formatters';
import { ApiEndpoints } from '../../../enums/ApiEndpoints';
import { ModelType } from '../../../enums/ModelType';
import { getDetailUrl } from '../../../functions/urls';
import { useInstance } from '../../../hooks/UseInstance';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { TableColumn } from '../../../tables/Column';
import { PartColumn } from '../../../tables/ColumnRenderers';
import { InvenTreeTable } from '../../../tables/InvenTreeTable';

const BOM_COLORS: string[] = [
  '#ffa8a8',
  '#8ce99a',
  '#74c0fc',
  '#ffe066',
  '#63e6be',
  '#ffc078',
  '#d8f5a2',
  '#66d9e8',
  '#e599f7',
  '#dee2e6'
];

export default function BomPricingPanel({
  part,
  pricing
}: {
  part: any;
  pricing: any;
}): ReactNode {
  const table = useTable('pricing-bom');

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Component`,
        sortable: true,
        switchable: false,
        render: (record: any) =>
          PartColumn(
            record.sub_part_detail,
            getDetailUrl(ModelType.part, record.sub_part_detail.pk)
          )
      },
      {
        accessor: 'quantity',
        title: t`Quantity`,
        sortable: true,
        switchable: false,
        render: (record: any) => formatDecimal(record.quantity)
      },
      {
        accessor: 'pricing_min',
        sortable: true,
        switchable: false,
        title: t`Minimum Price`,
        render: (record: any) =>
          formatCurrency(record.quantity * record.pricing_min, {
            currency: pricing?.currency
          })
      },
      {
        accessor: 'pricing_max',
        title: t`Maximum Price`,
        sortable: true,
        switchable: false,
        render: (record: any) =>
          formatCurrency(record.quantity * record.pricing_max, {
            currency: pricing?.currency
          })
      }
    ];
  }, [part, pricing]);

  const bomPricingData: any[] = useMemo(() => {
    const pricing = table.records.map((entry: any) => {
      return {
        entry: entry,
        quantity: entry.quantity,
        name: entry.sub_part_detail?.name,
        pmin: parseFloat(entry.pricing_min ?? entry.pricing_max ?? 0),
        pmax: parseFloat(entry.pricing_max ?? entry.pricing_min ?? 0)
      };
    });

    return pricing;
  }, [table.records]);

  // TODO: Enable record selection (toggle which items appear in BOM pricing wheel)
  // TODO: Display BOM entry colors in table, using custom rowStyle prop

  return (
    <Stack spacing="xs">
      <SimpleGrid cols={2}>
        <InvenTreeTable
          tableState={table}
          url={apiUrl(ApiEndpoints.bom_list)}
          columns={columns}
          props={{
            params: {
              part: part?.pk,
              sub_part_detail: true,
              has_pricing: true
            },
            enableSelection: false
          }}
        />
        <ResponsiveContainer width="100%" height={500}>
          <PieChart>
            <Pie
              data={bomPricingData}
              labelLine={false}
              dataKey="pmin"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={50}
              fill="#8884d8"
            >
              {bomPricingData.map((entry, index) => (
                <Cell
                  key={entry.name}
                  fill={BOM_COLORS[index % BOM_COLORS.length]}
                />
              ))}
            </Pie>
            <Pie
              data={bomPricingData}
              dataKey="pmax"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={80}
              fill="#82ca9d"
            >
              {bomPricingData.map((entry, index) => (
                <Cell
                  key={entry.name}
                  fill={BOM_COLORS[index % BOM_COLORS.length]}
                />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </SimpleGrid>
    </Stack>
  );
}
