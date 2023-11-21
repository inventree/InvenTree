import { t } from '@lingui/macro';
import { Divider, Paper, Stack } from '@mantine/core';

import { StylishText } from '../../components/items/StylishText';
import { useUserState } from '../../states/UserState';

function PricingGroup({
  children,
  title
}: {
  children?: React.ReactNode;
  title: string;
}) {
  return (
    <Paper radius="sm" p="md">
      <Stack spacing="xs">
        <StylishText size="xl">{title}</StylishText>
        <Divider />
        {children}
      </Stack>
    </Paper>
  );
}

/*
 * Render a pricing panel for a single part
 */
export function PartPricingPanel({ part }: { part: any }) {
  const user = useUserState();

  return (
    <Stack spacing="xs">
      <PricingGroup title={t`Pricing Overview`}></PricingGroup>
      <PricingGroup title={t`Internal Pricing`}></PricingGroup>
      {part.assembly && <PricingGroup title={t`BOM Pricing`}></PricingGroup>}
      {part.purchaseable && (
        <PricingGroup title={t`Supplier Pricing`}></PricingGroup>
      )}
      {part.purchaseable && (
        <PricingGroup title={t`Purchase History`}></PricingGroup>
      )}
      {part.salable && <PricingGroup title={t`Sale Pricing`}></PricingGroup>}
      {part.salable && <PricingGroup title={t`Sale History`}></PricingGroup>}
    </Stack>
  );
}
