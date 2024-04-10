import { t } from '@lingui/macro';
import { SimpleGrid, Stack } from '@mantine/core';
import { ReactNode, useMemo } from 'react';
import {
  Bar,
  BarChart,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

import { formatCurrency } from '../../../defaults/formatters';
import { ApiEndpoints } from '../../../enums/ApiEndpoints';
import { ModelType } from '../../../enums/ModelType';
import { getDetailUrl } from '../../../functions/urls';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { TableColumn } from '../../../tables/Column';
import { PartColumn } from '../../../tables/ColumnRenderers';
import { InvenTreeTable } from '../../../tables/InvenTreeTable';

export default function VariantPricingPanel({
  part,
  pricing
}: {
  part: any;
  pricing: any;
}): ReactNode {
  const table = useTable('pricing-variants');

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Variant Part`,
        sortable: true,
        switchable: false,
        render: (record: any) =>
          PartColumn(record, getDetailUrl(ModelType.part, record.pk))
      },
      {
        accessor: 'pricing_min',
        title: t`Minimum Price`,
        sortable: true,
        switchable: false,
        render: (record: any) =>
          formatCurrency(record.pricing_min, { currency: pricing?.currency })
      },
      {
        accessor: 'pricing_max',
        title: t`Maximum Price`,
        sortable: true,
        switchable: false,
        render: (record: any) =>
          formatCurrency(record.pricing_max, { currency: pricing?.currency })
      }
    ];
  }, []);

  // Calculate pricing data for the part variants
  const variantPricingData: any[] = useMemo(() => {
    const pricing = table.records.map((variant: any) => {
      return {
        part: variant,
        name: variant.full_name,
        pmin: variant.pricing_min ?? variant.pricing_max ?? 0,
        pmax: variant.pricing_max ?? variant.pricing_min ?? 0
      };
    });

    return pricing;
  }, [table.records]);

  return (
    <Stack spacing="xs">
      <SimpleGrid cols={2}>
        <InvenTreeTable
          tableState={table}
          url={apiUrl(ApiEndpoints.part_list)}
          columns={columns}
          props={{
            params: {
              ancestor: part?.pk,
              has_pricing: true
            },
            enablePagination: false
          }}
        />
        <ResponsiveContainer width="100%" height={500}>
          <BarChart data={variantPricingData}>
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="pmin" fill="#8884d8" label={t`Minimum Price`} />
            <Bar dataKey="pmax" fill="#82ca9d" label={t`Maximum Price`} />
          </BarChart>
        </ResponsiveContainer>
      </SimpleGrid>
    </Stack>
  );
}
