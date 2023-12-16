import { Trans, t } from '@lingui/macro';
import {
  Accordion,
  Divider,
  Group,
  Paper,
  Space,
  Stack,
  Table,
  Text
} from '@mantine/core';
import {
  IconBuildingStore,
  IconChartLine,
  IconClipboardData,
  IconTools,
  IconTruckDelivery
} from '@tabler/icons-react';
import {
  ArcElement,
  ChartData,
  Chart as ChartJS,
  Legend,
  Tooltip
} from 'chart.js';
import { Doughnut } from 'react-chartjs-2';

import { StylishText } from '../../components/items/StylishText';
import { formatCurrency } from '../../defaults/formatters';
import { ApiPaths } from '../../enums/ApiEndpoints';
import { useInstance } from '../../hooks/UseInstance';
import { useUserState } from '../../states/UserState';

ChartJS.register(ArcElement, Tooltip, Legend);

function PricingGroup({
  children,
  title,
  label
}: {
  children?: React.ReactNode;
  title: string;
  label: string;
}) {
  return (
    <Accordion.Item value={label}>
      <Accordion.Control>
        <StylishText size="md">{title}</StylishText>
      </Accordion.Control>
      <Accordion.Panel>{children}</Accordion.Panel>
    </Accordion.Item>
  );
}

function OverviewRow({
  title,
  min_cost,
  max_cost,
  currency
}: {
  title: string;
  min_cost: number | null;
  max_cost: number | null;
  currency: string;
}) {
  const no_data = <Text italic>{t`No data`}</Text>;

  return (
    <tr>
      <th>{title}</th>
      <td>{formatCurrency(min_cost, { currency: currency }) || no_data}</td>
      <td>{formatCurrency(max_cost, { currency: currency }) || no_data}</td>
    </tr>
  );
}

/*
 * Render a pricing panel for a single part
 */
export function PartPricingPanel({ part }: { part: any }) {
  const user = useUserState();

  const { instance: pricing, refreshInstance: refreshPricing } = useInstance({
    endpoint: ApiPaths.part_pricing_detail,
    pk: part.pk
  });

  const DATA_COUNT = 5;
  const NUMBER_CFG = { count: DATA_COUNT, min: 0, max: 100 };

  const data: ChartData = {
    labels: ['Red', 'Orange', 'Yellow', 'Green', 'Blue'],
    datasets: [
      {
        label: 'Dataset 1',
        data: [], // Utils.numbers(NUMBER_CFG),
        backgroundColor: '#F00' // Object.values(Utils.CHART_COLORS),
      }
    ]
  };

  return (
    <Stack spacing="xs">
      <Group position="left" spacing="sm" grow>
        <Stack align="stretch" justify="flex-start">
          <StylishText size="sm">{t`Cost Price`}</StylishText>
          <Table striped>
            <thead>
              <th>
                <Trans>Category</Trans>
              </th>
              <th>
                <Trans>Minimum</Trans>
              </th>
              <th>
                <Trans>Maximum</Trans>
              </th>
            </thead>
            <tbody>
              <OverviewRow
                title={t`Internal Pricing`}
                min_cost={pricing.internal_cost_min}
                max_cost={pricing.internal_cost_max}
                currency={pricing.currency}
              />
              <OverviewRow
                title={t`BOM Pricing`}
                min_cost={pricing.bom_cost_min}
                max_cost={pricing.bom_cost_max}
                currency={pricing.currency}
              />
              <OverviewRow
                title={t`Supplier Pricing`}
                min_cost={pricing.supplier_price_min}
                max_cost={pricing.supplier_price_max}
                currency={pricing.currency}
              />
              <OverviewRow
                title={t`Purchase History`}
                min_cost={pricing.purchase_cost_min}
                max_cost={pricing.purchase_cost_max}
                currency={pricing.currency}
              />
              <OverviewRow
                title={t`Overall Pricing`}
                min_cost={pricing.overall_min}
                max_cost={pricing.overall_min}
                currency={pricing.currency}
              />
            </tbody>
          </Table>
          <Space />
        </Stack>
        <Stack align="stretch" justify="flex-start">
          <StylishText size="sm">{t`Sale Price`}</StylishText>
          <Table striped>
            <thead>
              <th>
                <Trans>Category</Trans>
              </th>
              <th>
                <Trans>Minimum</Trans>
              </th>
              <th>
                <Trans>Maximum</Trans>
              </th>
            </thead>
            <tbody>
              <OverviewRow
                title={t`Internal Pricing`}
                min_cost={pricing.sale_price_min}
                max_cost={pricing.sale_price_max}
                currency={pricing.currency}
              />
              <OverviewRow
                title={t`Sale History`}
                min_cost={pricing.sale_history_min}
                max_cost={pricing.sale_history_max}
                currency={pricing.currency}
              />
            </tbody>
          </Table>
          <Space />
        </Stack>
      </Group>

      <Accordion defaultValue={['internal']} multiple>
        <PricingGroup
          title={t`Internal Pricing`}
          label="internal"
        ></PricingGroup>
        {part.assembly && (
          <PricingGroup title={t`BOM Pricing`} label="bom">
            <Group grow position="left" spacing="sm">
              <Doughnut data={data} />
            </Group>
          </PricingGroup>
        )}
        {part.purchaseable && (
          <PricingGroup
            title={t`Supplier Pricing`}
            label="supplier"
          ></PricingGroup>
        )}
        {part.purchaseable && (
          <PricingGroup
            title={t`Purchase History`}
            label="purchase"
          ></PricingGroup>
        )}
        {part.salable && (
          <PricingGroup title={t`Sale Pricing`} label="sales"></PricingGroup>
        )}
        {part.salable && (
          <PricingGroup
            title={t`Sale History`}
            label="saleshistory"
          ></PricingGroup>
        )}
      </Accordion>
    </Stack>
  );
}
