import { t } from '@lingui/macro';
import { LoadingOverlay, SimpleGrid, Stack } from '@mantine/core';
import { DataTable, DataTableColumn } from 'mantine-datatable';
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
import { useInstance } from '../../../hooks/UseInstance';
import { PartColumn } from '../../../tables/ColumnRenderers';

export default function VariantPricingPanel({
  part,
  pricing
}: {
  part: any;
  pricing: any;
}): ReactNode {
  const {
    instance: variants,
    refreshInstance,
    instanceQuery
  } = useInstance({
    hasPrimaryKey: false,
    endpoint: ApiEndpoints.part_list,
    params: {
      ancestor: part?.pk
    },
    defaultValue: []
  });

  // Calculate pricing data for the part variants
  const variantPricingData: any[] = useMemo(() => {
    const pricing = variants.map((variant: any) => {
      return {
        part: variant,
        name: variant.full_name,
        pmin: variant.pricing_min ?? variant.pricing_max ?? 0,
        pmax: variant.pricing_max ?? variant.pricing_min ?? 0
      };
    });

    return pricing;
  }, [variants]);

  const columns: DataTableColumn<any>[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Variant Part`,
        render: (record: any) =>
          PartColumn(record.part, getDetailUrl(ModelType.part, record.part.pk))
      },
      {
        accessor: 'pmin',
        title: t`Minimum Price`,
        render: (record: any) =>
          formatCurrency(record.pmin, { currency: pricing?.currency })
      },
      {
        accessor: 'pmax',
        title: t`Maximum Price`,
        render: (record: any) =>
          formatCurrency(record.pmax, { currency: pricing?.currency })
      }
    ];
  }, []);

  return (
    <Stack spacing="xs">
      <LoadingOverlay visible={instanceQuery.isLoading} />
      <SimpleGrid cols={2}>
        <DataTable records={variantPricingData} columns={columns} />
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
