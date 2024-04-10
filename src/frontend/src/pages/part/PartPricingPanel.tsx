import { t } from '@lingui/macro';
import { Accordion, Alert, LoadingOverlay, Stack, Text } from '@mantine/core';
import { ReactNode, useMemo } from 'react';

import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import { useInstance } from '../../hooks/UseInstance';
import { useUserState } from '../../states/UserState';
import BomPricingPanel from './pricing/BomPricingPanel';
import InternalPricingPanel from './pricing/InternalPricingPanel';
import PricingOverviewPanel from './pricing/PricingOverviewPanel';
import PricingPanel from './pricing/PricingPanel';
import PurchaseHistoryPanel from './pricing/PurchaseHistoryPanel';
import SupplierPricingPanel from './pricing/SupplierPricingPanel';
import VariantPricingPanel from './pricing/VariantPricingPanel';

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
            content={<PricingOverviewPanel part={part} pricing={pricing} />}
            label="overview"
            title={t`Pricing Overview`}
            visible={true}
          />
          <PricingPanel
            content={<PurchaseHistoryPanel part={part} />}
            label="purchase"
            title={t`Purchase History`}
            visible={purchaseOrderPricing}
          />
          <PricingPanel
            content={<InternalPricingPanel part={part} />}
            label="internal"
            title={t`Internal Pricing`}
            visible={internalPricing}
          />
          <PricingPanel
            content={<SupplierPricingPanel part={part} />}
            label="supplier"
            title={t`Supplier Pricing`}
            visible={purchaseOrderPricing}
          />
          <PricingPanel
            content={<BomPricingPanel part={part} pricing={pricing} />}
            label="bom"
            title={t`BOM Pricing`}
            visible={part?.assembly}
          />
          <PricingPanel
            content={<VariantPricingPanel part={part} pricing={pricing} />}
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
