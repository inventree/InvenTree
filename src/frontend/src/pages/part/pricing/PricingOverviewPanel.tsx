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
import { notifications } from '@mantine/notifications';
import {
  IconBuildingWarehouse,
  IconChartDonut,
  IconCircleCheck,
  IconExclamationCircle,
  IconList,
  IconReportAnalytics,
  IconShoppingCart,
  IconTriangleSquareCircle
} from '@tabler/icons-react';
import type { UseQueryResult } from '@tanstack/react-query';
import { DataTable } from 'mantine-datatable';
import { type ReactNode, useCallback, useMemo } from 'react';

import { api } from '../../../App';
import { tooltipFormatter } from '../../../components/charts/tooltipFormatter';
import type { ApiFormFieldSet } from '../../../components/forms/fields/ApiFormField';
import {
  EditItemAction,
  OptionsActionDropdown
} from '../../../components/items/ActionDropdown';
import { formatCurrency, formatDate } from '../../../defaults/formatters';
import { ApiEndpoints } from '../../../enums/ApiEndpoints';
import { InvenTreeIcon } from '../../../functions/icons';
import { useEditApiFormModal } from '../../../hooks/UseForm';
import { apiUrl } from '../../../states/ApiState';
import { useGlobalSettingsState } from '../../../states/SettingsState';
import { panelOptions } from '../PartPricingPanel';

interface PricingOverviewEntry {
  icon: ReactNode;
  name: panelOptions;
  title: string;
  valid: boolean;
  min_value: number | null | undefined;
  max_value: number | null | undefined;
  visible?: boolean;
  currency?: string | null | undefined;
}

export default function PricingOverviewPanel({
  part,
  pricing,
  pricingQuery,
  doNavigation
}: Readonly<{
  part: any;
  pricing: any;
  pricingQuery: UseQueryResult;
  doNavigation: (panel: panelOptions) => void;
}>): ReactNode {
  const globalSettings = useGlobalSettingsState();

  const refreshPricing = useCallback(() => {
    const url = apiUrl(ApiEndpoints.part_pricing, part.pk);

    notifications.hide('pricing-refresh');

    notifications.show({
      message: t`Refreshing pricing data`,
      color: 'green',
      id: 'pricing-refresh',
      loading: true,
      autoClose: false
    });

    let success = false;

    api
      .patch(url, { update: true })
      .then((response) => {
        success = response.status === 200;
      })
      .catch(() => {})
      .finally(() => {
        notifications.hide('pricing-refresh');

        if (success) {
          notifications.show({
            message: t`Pricing data updated`,
            color: 'green',
            icon: <IconCircleCheck />
          });
          pricingQuery.refetch();
        } else {
          notifications.show({
            message: t`Failed to update pricing data`,
            color: 'red',
            icon: <IconExclamationCircle />
          });
        }
      });
  }, [part]);

  const pricingFields: ApiFormFieldSet = useMemo(() => {
    return {
      override_min: {},
      override_min_currency: {
        default:
          globalSettings.getSetting('INVENTREE_DEFAULT_CURRENCY') ?? 'USD'
      },
      override_max: {},
      override_max_currency: {
        default:
          globalSettings.getSetting('INVENTREE_DEFAULT_CURRENCY') ?? 'USD'
      },
      update: {
        hidden: true,
        value: true
      }
    };
  }, [globalSettings]);

  const editPricing = useEditApiFormModal({
    title: t`Edit Pricing`,
    url: apiUrl(ApiEndpoints.part_pricing, part.pk),
    fields: pricingFields,
    onFormSuccess: () => {
      pricingQuery.refetch();
    }
  });

  const columns: any[] = useMemo(() => {
    return [
      {
        accessor: 'title',
        title: t`Pricing Category`,
        render: (record: PricingOverviewEntry) => {
          const is_link = record.name !== panelOptions.overall;
          return (
            <Group justify='left' gap='xs'>
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
        name: panelOptions.override,
        title: t`Override Pricing`,
        icon: <IconExclamationCircle />,
        min_value: Number.parseFloat(pricing?.override_min),
        max_value: Number.parseFloat(pricing?.override_max),
        valid: pricing?.override_min != null && pricing?.override_max != null
      },
      {
        name: panelOptions.overall,
        title: t`Overall Pricing`,
        icon: <IconReportAnalytics />,
        min_value: Number.parseFloat(pricing?.overall_min),
        max_value: Number.parseFloat(pricing?.overall_max),
        valid: pricing?.overall_min != null && pricing?.overall_max != null
      },
      {
        name: panelOptions.internal,
        title: t`Internal Pricing`,
        icon: <IconList />,
        min_value: Number.parseFloat(pricing?.internal_cost_min),
        max_value: Number.parseFloat(pricing?.internal_cost_max),
        valid:
          pricing?.internal_cost_min != null &&
          pricing?.internal_cost_max != null
      },
      {
        name: panelOptions.bom,
        title: t`BOM Pricing`,
        icon: <IconChartDonut />,
        min_value: Number.parseFloat(pricing?.bom_cost_min),
        max_value: Number.parseFloat(pricing?.bom_cost_max),
        valid: pricing?.bom_cost_min != null && pricing?.bom_cost_max != null
      },
      {
        name: panelOptions.purchase,
        title: t`Purchase Pricing`,
        icon: <IconShoppingCart />,
        min_value: Number.parseFloat(pricing?.purchase_cost_min),
        max_value: Number.parseFloat(pricing?.purchase_cost_max),
        valid:
          pricing?.purchase_cost_min != null &&
          pricing?.purchase_cost_max != null
      },
      {
        name: panelOptions.supplier,
        title: t`Supplier Pricing`,
        icon: <IconBuildingWarehouse />,
        min_value: Number.parseFloat(pricing?.supplier_price_min),
        max_value: Number.parseFloat(pricing?.supplier_price_max),
        valid:
          pricing?.supplier_price_min != null &&
          pricing?.supplier_price_max != null
      },
      {
        name: panelOptions.variant,
        title: t`Variant Pricing`,
        icon: <IconTriangleSquareCircle />,
        min_value: Number.parseFloat(pricing?.variant_cost_min),
        max_value: Number.parseFloat(pricing?.variant_cost_max),
        valid:
          pricing?.variant_cost_min != null && pricing?.variant_cost_max != null
      },
      {
        name: panelOptions.sale_pricing,
        title: t`Sale Pricing`,
        icon: <IconTriangleSquareCircle />,
        min_value: Number.parseFloat(pricing?.sale_price_min),
        max_value: Number.parseFloat(pricing?.sale_price_max),
        valid:
          pricing?.sale_price_min != null && pricing?.sale_price_max != null
      },
      {
        name: panelOptions.sale_history,
        title: t`Sale History`,
        icon: <IconTriangleSquareCircle />,
        min_value: Number.parseFloat(pricing?.sale_history_min),
        max_value: Number.parseFloat(pricing?.sale_history_max),
        valid:
          pricing?.sale_history_min != null && pricing?.sale_history_max != null
      }
    ].filter((entry) => {
      return entry.valid;
    });
  }, [part, pricing]);

  return (
    <>
      {editPricing.modal}
      <Stack gap='xs'>
        <SimpleGrid cols={{ base: 1, md: 2 }}>
          <Stack gap='xs'>
            <Paper p='xs'>
              <Group justify='space-between' wrap='nowrap'>
                {pricing?.updated ? (
                  <Alert color='blue' title={t`Last Updated`} flex={1}>
                    <Text>{formatDate(pricing.updated)}</Text>
                  </Alert>
                ) : (
                  <Alert color='orange' title={t`Pricing Not Set`} flex={1}>
                    <Text>{t`Pricing data has not been calculated for this part`}</Text>
                  </Alert>
                )}
                <OptionsActionDropdown
                  tooltip={t`Pricing Actions`}
                  actions={[
                    {
                      name: t`Refresh`,
                      tooltip: t`Refresh pricing data`,
                      icon: (
                        <InvenTreeIcon
                          icon='refresh'
                          iconProps={{ color: 'green' }}
                        />
                      ),
                      onClick: () => {
                        refreshPricing();
                      }
                    },
                    EditItemAction({
                      onClick: () => {
                        editPricing.open();
                      },
                      tooltip: t`Edit pricing data`
                    })
                  ]}
                />
              </Group>
            </Paper>
            <DataTable
              idAccessor='name'
              records={overviewData}
              columns={columns}
            />
          </Stack>
          <BarChart
            aria-label='pricing-overview-chart'
            dataKey='title'
            data={overviewData}
            title={t`Pricing Overview`}
            series={[
              { name: 'min_value', label: t`Minimum Value`, color: 'blue.6' },
              { name: 'max_value', label: t`Maximum Value`, color: 'teal.6' }
            ]}
            valueFormatter={(value) =>
              tooltipFormatter(value, pricing?.currency)
            }
          />
        </SimpleGrid>
      </Stack>
    </>
  );
}
