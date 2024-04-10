import { t } from '@lingui/macro';
import {
  Accordion,
  Alert,
  LoadingOverlay,
  SimpleGrid,
  Stack,
  Text
} from '@mantine/core';
import { DataTable, DataTableColumn } from 'mantine-datatable';
import { ReactNode, useMemo } from 'react';
import { Responsive } from 'react-grid-layout';
import {
  Bar,
  BarChart,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

import { StylishText } from '../../components/items/StylishText';
import { formatCurrency, formatDecimal } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { getDetailUrl } from '../../functions/urls';
import { useInstance } from '../../hooks/UseInstance';
import { useUserState } from '../../states/UserState';
import { PartColumn } from '../../tables/ColumnRenderers';

interface PricingOverviewEntry {
  name: string;
  title: string;
  min_value: number | null | undefined;
  max_value: number | null | undefined;
  visible?: boolean;
  currency?: string | null | undefined;
}

function PricingOverview({
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

function PurchaseHistory({
  part,
  pricing
}: {
  part: any;
  pricing: any;
}): ReactNode {
  return (
    <Stack spacing="xs">
      <Text>Purchase History goes here?</Text>
    </Stack>
  );
}

function SaleHistroy({
  part,
  pricing
}: {
  part: any;
  pricing: any;
}): ReactNode {
  return (
    <Stack spacing="xs">
      <Text>Sale History goes here?</Text>
    </Stack>
  );
}

function InternalPricing({
  part,
  pricing
}: {
  part: any;
  pricing: any;
}): ReactNode {
  return (
    <Stack spacing="xs">
      <Text>Internal Pricing goes here?</Text>
    </Stack>
  );
}

function SalePricing({
  part,
  pricing
}: {
  part: any;
  pricing: any;
}): ReactNode {
  return (
    <Stack spacing="xs">
      <Text>Sale Pricing goes here?</Text>
    </Stack>
  );
}

function SupplierPricing({
  part,
  pricing
}: {
  part: any;
  pricing: any;
}): ReactNode {
  return (
    <Stack spacing="xs">
      <Text>Supplier Pricing goes here?</Text>
    </Stack>
  );
}

function BomPricing({ part, pricing }: { part: any; pricing: any }): ReactNode {
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

function VariantPricing({
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

function PricingPanel({
  content,
  label,
  title,
  visible
}: {
  content: ReactNode;
  label: string;
  title: string;
  visible: boolean;
}): ReactNode {
  return (
    visible && (
      <Accordion.Item value={label}>
        <Accordion.Control>
          <StylishText size="lg">{title}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>{content}</Accordion.Panel>
      </Accordion.Item>
    )
  );
}

export default function PartPricingPanel({ part }: { part: any }) {
  const user = useUserState();

  const {
    instance: pricing,
    refreshInstance,
    instanceQuery
  } = useInstance({
    pk: part?.pk,
    hasPrimaryKey: true,
    endpoint: ApiEndpoints.part_pricing_get,
    defaultValue: {}
  });

  // TODO: Do we display internal price? This is a global setting
  const internalPricing = true;

  const purchaseOrderPricing = useMemo(() => {
    return user.hasViewRole(UserRoles.purchase_order) && part?.purchaseable;
  }, [user, part]);

  const salesOrderPricing = useMemo(() => {
    return user.hasViewRole(UserRoles.sales_order) && part?.salable;
  }, [user, part]);

  return (
    <Stack spacing="xs">
      <LoadingOverlay visible={instanceQuery.isLoading} />
      {!pricing && !instanceQuery.isLoading && (
        <Alert color="ref" title={t`Error`}>
          <Text>{t`No pricing data found for this part.`}</Text>
        </Alert>
      )}
      {pricing && (
        <Accordion multiple defaultValue={['overview']}>
          <PricingPanel
            content={<PricingOverview part={part} pricing={pricing} />}
            label="overview"
            title={t`Pricing Overview`}
            visible={true}
          />
          <PricingPanel
            content={<PurchaseHistory part={part} pricing={pricing} />}
            label="purchase"
            title={t`Purchase History`}
            visible={purchaseOrderPricing}
          />
          <PricingPanel
            content={<InternalPricing part={part} pricing={pricing} />}
            label="internal"
            title={t`Internal Pricing`}
            visible={internalPricing}
          />
          <PricingPanel
            content={<SupplierPricing part={part} pricing={pricing} />}
            label="supplier"
            title={t`Supplier Pricing`}
            visible={purchaseOrderPricing}
          />
          <PricingPanel
            content={<BomPricing part={part} pricing={pricing} />}
            label="bom"
            title={t`BOM Pricing`}
            visible={part?.assembly}
          />
          <PricingPanel
            content={<VariantPricing part={part} pricing={pricing} />}
            label="variant"
            title={t`Variant Pricing`}
            visible={part?.is_template}
          />
          <PricingPanel
            content={<SalePricing part={part} pricing={pricing} />}
            label="sale"
            title={t`Sale Pricing`}
            visible={salesOrderPricing}
          />
          <PricingPanel
            content={<SaleHistroy part={part} pricing={pricing} />}
            label="sale"
            title={t`Sale History`}
            visible={salesOrderPricing}
          />
        </Accordion>
      )}
    </Stack>
  );
}
