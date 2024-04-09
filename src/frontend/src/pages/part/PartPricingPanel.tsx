import { t } from '@lingui/macro';
import { Accordion, Alert, LoadingOverlay, Stack, Text } from '@mantine/core';
import { ReactNode, useMemo } from 'react';

import { StylishText } from '../../components/items/StylishText';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import { useInstance } from '../../hooks/UseInstance';
import { useUserState } from '../../states/UserState';

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
  return (
    <Stack spacing="xs">
      <Text>Variant Pricing goes here?</Text>
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
            content={<SaleHistroy part={part} pricing={pricing} />}
            label="sale"
            title={t`Sale History`}
            visible={salesOrderPricing}
          />
          <PricingPanel
            content={<InternalPricing part={part} pricing={pricing} />}
            label="internal"
            title={t`Internal Pricing`}
            visible={internalPricing}
          />
          <PricingPanel
            content={<SalePricing part={part} pricing={pricing} />}
            label="sale"
            title={t`Sale Pricing`}
            visible={salesOrderPricing}
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
        </Accordion>
      )}
    </Stack>
  );
}
