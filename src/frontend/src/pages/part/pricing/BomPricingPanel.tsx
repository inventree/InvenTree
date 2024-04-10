import { t } from '@lingui/macro';
import { LoadingOverlay, SimpleGrid, Stack } from '@mantine/core';
import { DataTable, DataTableColumn } from 'mantine-datatable';
import { ReactNode, useMemo } from 'react';
import { Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';

import { formatCurrency, formatDecimal } from '../../../defaults/formatters';
import { ApiEndpoints } from '../../../enums/ApiEndpoints';
import { ModelType } from '../../../enums/ModelType';
import { getDetailUrl } from '../../../functions/urls';
import { useInstance } from '../../../hooks/UseInstance';
import { PartColumn } from '../../../tables/ColumnRenderers';

export default function BomPricingPanel({
  part,
  pricing
}: {
  part: any;
  pricing: any;
}): ReactNode {
  const {
    instance: bomData,
    refreshInstance,
    instanceQuery
  } = useInstance({
    hasPrimaryKey: false,
    endpoint: ApiEndpoints.bom_list,
    params: {
      part: part?.pk,
      has_pricing: true,
      sub_part_detail: true
    },
    defaultValue: []
  });

  const bomPricingData: any[] = useMemo(() => {
    const pricing = bomData.map((entry: any) => {
      return {
        entry: entry,
        quantity: entry.quantity,
        name: entry.sub_part_detail?.name,
        pmin: parseFloat(entry.pricing_min ?? entry.pricing_max ?? 0),
        pmax: parseFloat(entry.pricing_max ?? entry.pricing_min ?? 0)
      };
    });

    return pricing;
  }, [part, pricing, bomData]);

  const columns: DataTableColumn<any>[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Component`,
        render: (record: any) =>
          PartColumn(
            record.entry.sub_part_detail,
            getDetailUrl(ModelType.part, record.entry.sub_part_detail.pk)
          )
      },
      {
        accessor: 'quantity',
        title: t`Quantity`,
        render: (record: any) => formatDecimal(record.quantity)
      },
      {
        accessor: 'pmin',
        title: t`Minimum Price`,
        render: (record: any) =>
          formatCurrency(record.quantity * record.pmin, {
            currency: pricing?.currency
          })
      },
      {
        accessor: 'pmax',
        title: t`Maximum Price`,
        render: (record: any) =>
          formatCurrency(record.quantity * record.pmax, {
            currency: pricing?.currency
          })
      }
    ];
  }, [part, pricing]);

  // TODO: Enable record selection (toggle which items appear in BOM pricing wheel)
  // TODO: Different colors for each element in the pie chart
  // TODO: Display color next to each row in table

  return (
    <Stack spacing="xs">
      <LoadingOverlay visible={instanceQuery.isLoading} />
      <SimpleGrid cols={2}>
        <DataTable records={bomPricingData} columns={columns} />
        <ResponsiveContainer width="100%" height={500}>
          <PieChart>
            <Pie
              data={bomPricingData}
              dataKey="pmin"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={50}
              fill="#8884d8"
            />
            <Pie
              data={bomPricingData}
              dataKey="pmax"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={80}
              fill="#82ca9d"
            />
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </SimpleGrid>
    </Stack>
  );
}
