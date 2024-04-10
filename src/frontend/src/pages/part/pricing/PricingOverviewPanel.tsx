import { t } from '@lingui/macro';
import { SimpleGrid, Stack } from '@mantine/core';
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

interface PricingOverviewEntry {
  name: string;
  title: string;
  min_value: number | null | undefined;
  max_value: number | null | undefined;
  visible?: boolean;
  currency?: string | null | undefined;
}

export default function PricingOverviewPanel({
  part,
  pricing
}: {
  part: any;
  pricing: any;
}): ReactNode {
  const columns: DataTableColumn<any>[] = useMemo(() => {
    return [
      {
        accessor: 'title',
        title: t`Pricing Category`
      },
      {
        accessor: 'min_value',
        title: t`Minimum`,
        render: (record: PricingOverviewEntry) => {
          return formatCurrency(record?.min_value, {
            currency: record.currency ?? pricing?.currency
          });
        }
      },
      {
        accessor: 'max_value',
        title: t`Maximum`,
        render: (record: PricingOverviewEntry) => {
          return formatCurrency(record?.max_value, {
            currency: record.currency ?? pricing?.currency
          });
        }
      }
    ];
  }, [part, pricing]);

  const overviewData: PricingOverviewEntry[] = useMemo(() => {
    return [
      {
        name: 'internal',
        title: t`Internal Pricing`,
        min_value: pricing?.internal_min,
        max_value: pricing?.internal_max
      },
      {
        name: 'bom',
        title: t`BOM Pricing`,
        min_value: pricing?.bom_cost_min,
        max_value: pricing?.bom_cost_max
      },
      {
        name: 'purchase',
        title: t`Purchase Pricing`,
        min_value: pricing?.purchase_cost_min,
        max_value: pricing?.purchase_cost_max
      },
      {
        name: 'supplier',
        title: t`Supplier Pricing`,
        min_value: pricing?.supplier_price_min,
        max_value: pricing?.supplier_price_max
      },
      {
        name: 'variants',
        title: t`Variant Pricing`,
        min_value: pricing?.variant_cost_min,
        max_value: pricing?.variant_cost_max
      },
      {
        name: 'overall',
        title: t`Overall Pricing`,
        min_value: pricing?.overall_min,
        max_value: pricing?.overall_max
      }
    ];
  }, [part, pricing]);

  // TODO: Add display of "last updated"
  // TODO: Add "update now" button

  return (
    <Stack spacing="xs">
      <SimpleGrid cols={2}>
        <DataTable records={overviewData} columns={columns} />
        <ResponsiveContainer width="100%" height={500}>
          <BarChart data={overviewData}>
            <XAxis dataKey="title" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="min_value" fill="#8884d8" label={t`Minimum Price`} />
            <Bar dataKey="max_value" fill="#82ca9d" label={t`Maximum Price`} />
          </BarChart>
        </ResponsiveContainer>
      </SimpleGrid>
    </Stack>
  );
}
