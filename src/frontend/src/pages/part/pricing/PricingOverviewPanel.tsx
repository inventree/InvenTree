import { t } from '@lingui/macro';
import { BarChart } from '@mantine/charts';
import {
  Alert,
  Anchor,
  Group,
  Paper,
  SimpleGrid,
  Stack,
  Text
} from '@mantine/core';
import {
  IconBuildingWarehouse,
  IconChartDonut,
  IconExclamationCircle,
  IconList,
  IconReportAnalytics,
  IconShoppingCart,
  IconTriangleSquareCircle
} from '@tabler/icons-react';
import { DataTable } from 'mantine-datatable';
import { ReactNode, useMemo } from 'react';

import { tooltipFormatter } from '../../../components/charts/tooltipFormatter';
import { formatCurrency, formatDate } from '../../../defaults/formatters';
import { panelOptions } from '../PartPricingPanel';

interface PricingOverviewEntry {
  icon: ReactNode;
  name: panelOptions;
  title: string;
  min_value: number | null | undefined;
  max_value: number | null | undefined;
  visible?: boolean;
  currency?: string | null | undefined;
}

export default function PricingOverviewPanel({
  part,
  pricing,
  doNavigation
}: {
  part: any;
  pricing: any;
  doNavigation: (panel: panelOptions) => void;
}): ReactNode {
  const columns: any[] = useMemo(() => {
    return [
      {
        accessor: 'title',
        title: t`Pricing Category`,
        render: (record: PricingOverviewEntry) => {
          const is_link = record.name !== panelOptions.overall;
          return (
            <Group justify="left" gap="xs">
              {record.icon}
              {is_link ? (
                <Anchor fw={700} onClick={() => doNavigation(record.name)}>
                  {record.title}
                </Anchor>
              ) : (
                <Text fw={700}>{record.title}</Text>
              )}
            </Group>
          );
        }
      },
      {
        accessor: 'min_value',
        title: t`Minimum`,
        render: (record: PricingOverviewEntry) => {
          if (record?.min_value === null || record?.min_value === undefined) {
            return '-';
          }
          return formatCurrency(record?.min_value, {
            currency: record.currency ?? pricing?.currency
          });
        }
      },
      {
        accessor: 'max_value',
        title: t`Maximum`,
        render: (record: PricingOverviewEntry) => {
          if (record?.max_value === null || record?.max_value === undefined) {
            return '-';
          }

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
        name: panelOptions.internal,
        title: t`Internal Pricing`,
        icon: <IconList />,
        min_value: pricing?.internal_cost_min,
        max_value: pricing?.internal_cost_max
      },
      {
        name: panelOptions.bom,
        title: t`BOM Pricing`,
        icon: <IconChartDonut />,
        min_value: pricing?.bom_cost_min,
        max_value: pricing?.bom_cost_max
      },
      {
        name: panelOptions.purchase,
        title: t`Purchase Pricing`,
        icon: <IconShoppingCart />,
        min_value: pricing?.purchase_cost_min,
        max_value: pricing?.purchase_cost_max
      },
      {
        name: panelOptions.supplier,
        title: t`Supplier Pricing`,
        icon: <IconBuildingWarehouse />,
        min_value: pricing?.supplier_price_min,
        max_value: pricing?.supplier_price_max
      },
      {
        name: panelOptions.variant,
        title: t`Variant Pricing`,
        icon: <IconTriangleSquareCircle />,
        min_value: pricing?.variant_cost_min,
        max_value: pricing?.variant_cost_max
      },
      {
        name: panelOptions.sale_pricing,
        title: t`Sale Pricing`,
        icon: <IconTriangleSquareCircle />,
        min_value: pricing?.sale_price_min,
        max_value: pricing?.sale_price_max
      },
      {
        name: panelOptions.sale_history,
        title: t`Sale History`,
        icon: <IconTriangleSquareCircle />,
        min_value: pricing?.sale_history_min,
        max_value: pricing?.sale_history_max
      },
      {
        name: panelOptions.override,
        title: t`Override Pricing`,
        icon: <IconExclamationCircle />,
        min_value: pricing?.override_min,
        max_value: pricing?.override_max
      },
      {
        name: panelOptions.overall,
        title: t`Overall Pricing`,
        icon: <IconReportAnalytics />,
        min_value: pricing?.overall_min,
        max_value: pricing?.overall_max
      }
    ].filter((entry) => {
      return !(entry.min_value == null || entry.max_value == null);
    });
  }, [part, pricing]);

  // TODO: Add display of "last updated"
  // TODO: Add "update now" button

  return (
    <Stack gap="xs">
      <SimpleGrid cols={2}>
        <Stack gap="xs">
          {pricing?.updated && (
            <Paper p="xs">
              <Alert color="blue" title={t`Last Updated`}>
                <Text>{formatDate(pricing.updated)}</Text>
              </Alert>
            </Paper>
          )}
          <DataTable
            idAccessor="name"
            records={overviewData}
            columns={columns}
          />
        </Stack>
        <BarChart
          aria-label="pricing-overview-chart"
          dataKey="title"
          data={overviewData}
          title={t`Pricing Overview`}
          series={[
            { name: 'min_value', label: t`Minimum Value`, color: 'blue.6' },
            { name: 'max_value', label: t`Maximum Value`, color: 'teal.6' }
          ]}
          valueFormatter={(value) => tooltipFormatter(value, pricing?.currency)}
        />
      </SimpleGrid>
    </Stack>
  );
}
