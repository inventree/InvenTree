import { t } from '@lingui/macro';
import { Accordion, Alert, LoadingOverlay, Stack, Text } from '@mantine/core';
import { useMemo, useState } from 'react';

import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import { useInstance } from '../../hooks/UseInstance';
import { useGlobalSettingsState } from '../../states/SettingsState';
import { useUserState } from '../../states/UserState';
import BomPricingPanel from './pricing/BomPricingPanel';
import PriceBreakPanel from './pricing/PriceBreakPanel';
import PricingOverviewPanel from './pricing/PricingOverviewPanel';
import PricingPanel from './pricing/PricingPanel';
import PurchaseHistoryPanel from './pricing/PurchaseHistoryPanel';
import SaleHistoryPanel from './pricing/SaleHistoryPanel';
import SupplierPricingPanel from './pricing/SupplierPricingPanel';
import VariantPricingPanel from './pricing/VariantPricingPanel';

export enum panelOptions {
  overview = 'overview',
  purchase = 'purchase',
  internal = 'internal',
  supplier = 'supplier',
  bom = 'bom',
  variant = 'variant',
  sale_pricing = 'sale-pricing',
  sale_history = 'sale-history',
  override = 'override',
  overall = 'overall'
}

export default function PartPricingPanel({ part }: Readonly<{ part: any }>) {
  const user = useUserState();

  const globalSettings = useGlobalSettingsState();

  const { instance: pricing, instanceQuery } = useInstance({
    pk: part?.pk,
    hasPrimaryKey: true,
    endpoint: ApiEndpoints.part_pricing,
    defaultValue: {}
  });

  const internalPricing: boolean = useMemo(() => {
    return globalSettings.isSet('PART_INTERNAL_PRICE');
  }, [globalSettings]);

  const purchaseOrderPricing = useMemo(() => {
    return user.hasViewRole(UserRoles.purchase_order) && part?.purchaseable;
  }, [user, part]);

  const salesOrderPricing = useMemo(() => {
    return user.hasViewRole(UserRoles.sales_order) && part?.salable;
  }, [user, part]);

  const [value, setValue] = useState<string[]>([panelOptions.overview]);
  function doNavigation(panel: panelOptions) {
    if (!value.includes(panel)) {
      setValue([...value, panel]);
    }
    const element = document.getElementById(panel);
    if (element) {
      element.scrollIntoView();
    }
  }

  return (
    <Stack gap='xs'>
      <LoadingOverlay visible={instanceQuery.isLoading} />
      {!pricing && !instanceQuery.isLoading && (
        <Alert color='ref' title={t`Error`}>
          <Text>{t`No pricing data found for this part.`}</Text>
        </Alert>
      )}
      {pricing && (
        <Accordion multiple value={value} onChange={setValue}>
          <PricingPanel
            content={
              <PricingOverviewPanel
                part={part}
                pricing={pricing}
                pricingQuery={instanceQuery}
                doNavigation={doNavigation}
              />
            }
            label={panelOptions.overview}
            title={t`Pricing Overview`}
            visible={true}
          />
          <PricingPanel
            content={<PurchaseHistoryPanel part={part} />}
            label={panelOptions.purchase}
            title={t`Purchase History`}
            visible={purchaseOrderPricing}
            disabled={
              !pricing?.purchase_cost_min || !pricing?.purchase_cost_max
            }
          />
          <PricingPanel
            content={
              <PriceBreakPanel
                part={part}
                endpoint={ApiEndpoints.part_pricing_internal}
              />
            }
            label={panelOptions.internal}
            title={t`Internal Pricing`}
            visible={internalPricing}
            disabled={
              !pricing?.internal_cost_min || !pricing?.internal_cost_max
            }
          />
          <PricingPanel
            content={<SupplierPricingPanel part={part} />}
            label={panelOptions.supplier}
            title={t`Supplier Pricing`}
            visible={purchaseOrderPricing}
            disabled={
              !pricing?.supplier_price_min || !pricing?.supplier_price_max
            }
          />
          <PricingPanel
            content={<BomPricingPanel part={part} pricing={pricing} />}
            label={panelOptions.bom}
            title={t`BOM Pricing`}
            visible={part?.assembly}
            disabled={!pricing?.bom_cost_min || !pricing?.bom_cost_max}
          />
          <PricingPanel
            content={<VariantPricingPanel part={part} pricing={pricing} />}
            label={panelOptions.variant}
            title={t`Variant Pricing`}
            visible={part?.is_template}
            disabled={!pricing?.variant_cost_min || !pricing?.variant_cost_max}
          />
          <PricingPanel
            content={
              <PriceBreakPanel
                part={part}
                endpoint={ApiEndpoints.part_pricing_sale}
              />
            }
            label={panelOptions.sale_pricing}
            title={t`Sale Pricing`}
            visible={salesOrderPricing}
            disabled={!pricing?.sale_price_min || !pricing?.sale_price_max}
          />
          <PricingPanel
            content={<SaleHistoryPanel part={part} />}
            label={panelOptions.sale_history}
            title={t`Sale History`}
            visible={salesOrderPricing}
            disabled={!pricing?.sale_history_min || !pricing?.sale_history_max}
          />
        </Accordion>
      )}
    </Stack>
  );
}
