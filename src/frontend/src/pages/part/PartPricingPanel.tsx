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
import {
  Bar,
  BarChart,
  Legend,
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

function PricingOverview({
  part,
  pricing
}: {
  part: any;
  pricing: any;
}): ReactNode {
  return (
    <Stack spacing="xs">
      <Text>Overview goes here?</Text>
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
  return (
    <Stack spacing="xs">
      <Text>BOM Pricing goes here?</Text>
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
    return variants.map((variant: any) => {
      return {
        part: variant,
        name: variant.full_name,
        pmin: formatDecimal(variant.pricing_min ?? variant.pricing_max ?? 0),
        pmax: formatDecimal(variant.pricing_max ?? variant.pricing_min ?? 0)
      };
    });
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
        <DataTable records={variantPricingData} columns={columns} />
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
