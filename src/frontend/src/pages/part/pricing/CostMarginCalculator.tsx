import { t } from '@lingui/core/macro';
import {
  ActionIcon,
  Alert,
  Badge,
  Box,
  Button,
  Card,
  Divider,
  Group,
  NumberInput,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  ThemeIcon,
  Tooltip
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconArrowRight,
  IconCalculator,
  IconCircleCheck,
  IconCoins,
  IconCurrencyDollar,
  IconDeviceFloppy,
  IconExclamationCircle,
  IconInfoCircle,
  IconPercentage,
  IconRefresh,
  IconSparkles,
  IconTrendingUp
} from '@tabler/icons-react';
import type { UseQueryResult } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { api } from '../../../App';
import { formatCurrency } from '../../../defaults/formatters';
import { useGlobalSettingsState } from '../../../states/SettingsStates';

export interface CostMarginCalculatorProps {
  part: any;
  pricing: any;
  pricingQuery?: UseQueryResult;
}

export default function CostMarginCalculator({
  part,
  pricing,
  pricingQuery
}: Readonly<CostMarginCalculatorProps>) {
  const globalSettings = useGlobalSettingsState();
  const defaultCurrency =
    globalSettings.getSetting('INVENTREE_DEFAULT_CURRENCY') ?? 'USD';

  // Currency
  const currency =
    pricing?.currency ||
    part?.cost_currency ||
    part?.metadata?.cost_currency ||
    defaultCurrency;

  // Initial cost discovery (from part direct field, metadata, or historical min pricing)
  const initialCost = useMemo(() => {
    if (part?.cost != null) return Number(part.cost);
    if (part?.metadata?.cost != null) return Number(part.metadata.cost);
    if (pricing?.override_min != null) return Number(pricing.override_min);
    if (pricing?.bom_cost_min != null) return Number(pricing.bom_cost_min);
    if (pricing?.purchase_cost_min != null)
      return Number(pricing.purchase_cost_min);
    if (pricing?.supplier_price_min != null)
      return Number(pricing.supplier_price_min);
    return '';
  }, [part, pricing]);

  // Initial margin discovery
  const initialMargin = useMemo(() => {
    if (part?.desired_margin != null) return Number(part.desired_margin);
    if (part?.metadata?.desired_margin != null)
      return Number(part.metadata.desired_margin);
    return '';
  }, [part]);

  // Initial selling price discovery
  const initialSellingPrice = useMemo(() => {
    if (part?.selling_price != null) return Number(part.selling_price);
    if (part?.metadata?.selling_price != null)
      return Number(part.metadata.selling_price);
    
    // Check for explicit 1-unit base price break
    if (part?.price_breaks && Array.isArray(part.price_breaks)) {
      const baseBreak = part.price_breaks.find(
        (pb: any) => Number(pb.quantity) === 1
      );
      if (baseBreak?.price != null) return Number(baseBreak.price);
    }

    // Default to maximum single-unit sale price if bulk discount tiers exist
    if (pricing?.sale_price_max != null) return Number(pricing.sale_price_max);
    if (pricing?.sale_price_min != null) return Number(pricing.sale_price_min);
    return '';
  }, [part, pricing]);

  // Initial minimum price discovery
  const initialMinimumPrice = useMemo(() => {
    if (part?.minimum_price != null) return Number(part.minimum_price);
    if (part?.metadata?.minimum_price != null)
      return Number(part.metadata.minimum_price);
    return '';
  }, [part]);

  // State
  const [cost, setCost] = useState<number | string>(initialCost);
  const [margin, setMargin] = useState<number | string>(initialMargin);
  const [sellingPrice, setSellingPrice] = useState<number | string>(
    initialSellingPrice
  );
  const [minPrice, setMinPrice] = useState<number | string>(initialMinimumPrice);
  const [saving, setSaving] = useState<boolean>(false);
  const [lastModified, setLastModified] = useState<
    'cost' | 'margin' | 'price' | null
  >(null);

  // Sync state when props change
  useEffect(() => {
    setCost(initialCost);
  }, [initialCost]);

  useEffect(() => {
    setMargin(initialMargin);
  }, [initialMargin]);

  useEffect(() => {
    setSellingPrice(initialSellingPrice);
  }, [initialSellingPrice]);

  useEffect(() => {
    setMinPrice(initialMinimumPrice);
  }, [initialMinimumPrice]);

  // 1. Reactive calculation when COST changes:
  // "If the cost changes while the margin remains the same, the selling price should automatically update."
  const handleCostChange = useCallback(
    (newCost: number | string) => {
      setCost(newCost);
      setLastModified('cost');

      const numCost = typeof newCost === 'number' ? newCost : parseFloat(newCost);
      const numMargin = typeof margin === 'number' ? margin : parseFloat(margin as string);

      if (!isNaN(numCost) && numCost >= 0) {
        if (!isNaN(numMargin) && numMargin < 100) {
          // Gross Margin: Price = Cost / (1 - Margin/100)
          const computedPrice = numCost / (1 - numMargin / 100);
          setSellingPrice(parseFloat(computedPrice.toFixed(4)));
        } else {
          const numPrice =
            typeof sellingPrice === 'number'
              ? sellingPrice
              : parseFloat(sellingPrice as string);
          if (!isNaN(numPrice) && numPrice > 0) {
            // Price is fixed, recompute margin: Margin = (Price - Cost) / Price * 100
            const computedMargin = ((numPrice - numCost) / numPrice) * 100;
            setMargin(parseFloat(computedMargin.toFixed(2)));
          }
        }
      }
    },
    [margin, sellingPrice]
  );

  // 2. Reactive calculation when DESIRED MARGIN changes:
  const handleMarginChange = useCallback(
    (newMargin: number | string) => {
      setMargin(newMargin);
      setLastModified('margin');

      const numCost = typeof cost === 'number' ? cost : parseFloat(cost as string);
      const numMargin =
        typeof newMargin === 'number' ? newMargin : parseFloat(newMargin as string);

      if (!isNaN(numCost) && numCost >= 0 && !isNaN(numMargin) && numMargin < 100) {
        // Price = Cost / (1 - Margin/100)
        const computedPrice = numCost / (1 - numMargin / 100);
        setSellingPrice(parseFloat(computedPrice.toFixed(4)));
      }
    },
    [cost]
  );

  // 3. Reactive calculation when SELLING PRICE changes:
  const handlePriceChange = useCallback(
    (newPrice: number | string) => {
      setSellingPrice(newPrice);
      setLastModified('price');

      const numCost = typeof cost === 'number' ? cost : parseFloat(cost as string);
      const numPrice =
        typeof newPrice === 'number' ? newPrice : parseFloat(newPrice as string);

      if (!isNaN(numCost) && !isNaN(numPrice) && numPrice > 0) {
        // Margin = (Price - Cost) / Price * 100
        const computedMargin = ((numPrice - numCost) / numPrice) * 100;
        setMargin(parseFloat(computedMargin.toFixed(2)));
      }
    },
    [cost]
  );

  // Financial Metrics
  const metrics = useMemo(() => {
    const numCost = typeof cost === 'number' ? cost : parseFloat(cost as string);
    const numPrice =
      typeof sellingPrice === 'number'
        ? sellingPrice
        : parseFloat(sellingPrice as string);

    if (isNaN(numCost) || isNaN(numPrice)) {
      return null;
    }

    const profit = numPrice - numCost;
    const grossMargin = numPrice > 0 ? (profit / numPrice) * 100 : 0;
    const markup = numCost > 0 ? (profit / numCost) * 100 : 0;

    const marginColor = grossMargin < 0 ? 'red' : 'blue';

    return {
      profit,
      grossMargin,
      markup,
      marginColor
    };
  }, [cost, sellingPrice]);

  // Quick helper buttons (Auto-fill cost from known pricing sources)
  const bomCost = pricing?.bom_cost_min ? Number(pricing.bom_cost_min) : null;
  const purchaseCost = pricing?.purchase_cost_min
    ? Number(pricing.purchase_cost_min)
    : null;
  const supplierCost = pricing?.supplier_price_min
    ? Number(pricing.supplier_price_min)
    : null;

  // Save changes
  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      const numCost =
        typeof cost === 'number' ? cost : cost !== '' ? parseFloat(cost) : null;
      const numMargin =
        typeof margin === 'number'
          ? margin
          : margin !== ''
          ? parseFloat(margin)
          : null;
      const numPrice =
        typeof sellingPrice === 'number'
          ? sellingPrice
          : sellingPrice !== ''
          ? parseFloat(sellingPrice)
          : null;
      const numMinPrice =
        typeof minPrice === 'number'
          ? minPrice
          : minPrice !== ''
          ? parseFloat(minPrice)
          : null;

      // 1. Persist directly to Part model fields (and metadata for backward compatibility)
      const existingMetadata = part?.metadata || {};
      const newMetadata = {
        ...existingMetadata,
        cost: numCost,
        desired_margin: numMargin,
        selling_price: numPrice,
        minimum_price: numMinPrice,
        cost_currency: currency,
        selling_price_currency: currency,
        minimum_price_currency: currency
      };

      await api.patch(apiUrl(ApiEndpoints.part_list, part.pk), {
        cost: numCost,
        cost_currency: currency,
        desired_margin: numMargin,
        selling_price: numPrice,
        selling_price_currency: currency,
        minimum_price: numMinPrice,
        minimum_price_currency: currency,
        metadata: newMetadata
      });

      // Update local part object so current view reflects it immediately
      if (part) {
        part.cost = numCost;
        part.cost_currency = currency;
        part.desired_margin = numMargin;
        part.selling_price = numPrice;
        part.selling_price_currency = currency;
        part.minimum_price = numMinPrice;
        part.minimum_price_currency = currency;
        part.metadata = newMetadata;
      }

      // 2. Also set override cost on PartPricing so InvenTree's internal overall_min / pricing_min reflects this cost
      if (numCost != null && numCost > 0) {
        try {
          await api.patch(apiUrl(ApiEndpoints.part_pricing, part.pk), {
            override_min: numCost,
            override_min_currency: currency,
            override_max: numCost,
            override_max_currency: currency
          });
        } catch (overrideErr) {
          console.warn('Could not update pricing override:', overrideErr);
        }
      }

      // 3. Also sync baseline price break (qty=1) if selling price is defined
      if (numPrice != null && numPrice > 0) {
        try {
          const pbResponse = await api.get(
            apiUrl(ApiEndpoints.part_pricing_sale),
            {
              params: { part: part.pk, quantity: 1 }
            }
          );

          if (pbResponse.data && pbResponse.data.length > 0) {
            const pbId = pbResponse.data[0].pk;
            await api.patch(apiUrl(ApiEndpoints.part_pricing_sale, pbId), {
              price: numPrice,
              price_currency: currency
            });
          } else {
            await api.post(apiUrl(ApiEndpoints.part_pricing_sale), {
              part: part.pk,
              quantity: 1,
              price: numPrice,
              price_currency: currency
            });
          }
        } catch (pbErr) {
          // Non-fatal if price breaks are restricted
          console.warn('Could not auto-sync sale price break:', pbErr);
        }
      }

      notifications.show({
        id: 'pricing-calc-save',
        color: 'green',
        icon: <IconCircleCheck />,
        title: t`Pricing Saved`,
        message: t`Cost, margin, and selling price have been saved successfully.`
      });

      pricingQuery?.refetch();
    } catch (err: any) {
      notifications.show({
        id: 'pricing-calc-error',
        color: 'red',
        icon: <IconExclamationCircle />,
        title: t`Error Saving Pricing`,
        message:
          err?.response?.data?.detail ||
          t`An error occurred while saving pricing data.`
      });
    } finally {
      setSaving(false);
    }
  }, [cost, margin, sellingPrice, currency, part, pricingQuery]);

  return (
    <Card
      withBorder
      shadow='sm'
      radius='md'
      p='md'
      style={{
        background:
          'linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.08) 100%)',
        borderColor: 'var(--mantine-color-blue-6)'
      }}
    >
      <Stack gap='sm'>
        {/* Header */}
        <Group justify='space-between' wrap='wrap'>
          <Group gap='xs'>
            <ThemeIcon size='lg' radius='md' variant='light' color='blue'>
              <IconCalculator size='1.3rem' />
            </ThemeIcon>
            <Box>
              <Group gap='xs'>
                <Text fw={700} size='md'>
                  {t`Cost, Margin & Selling Price Calculator`}
                </Text>
                <Badge variant='dot' color='blue' size='sm'>
                  {t`Auto-Calculating`}
                </Badge>
              </Group>
              <Text size='xs' c='dimmed'>
                {t`Update cost to automatically recompute the selling price while preserving the desired profit margin.`}
              </Text>
            </Box>
          </Group>

          <Button
            size='xs'
            leftSection={<IconDeviceFloppy size='0.9rem' />}
            onClick={handleSave}
            loading={saving}
            color='blue'
            variant='filled'
          >
            {t`Save Pricing`}
          </Button>
        </Group>

        <Divider />

        {/* Interactive Inputs */}
        <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }} spacing='md'>
          {/* 1. Cost Input */}
          <Paper p='xs' withBorder radius='sm'>
            <Stack gap='4px'>
              <Group justify='space-between'>
                <Text size='xs' fw={600} c='dimmed'>
                  {t`Unit Cost`}
                </Text>
                <Badge size='xs' variant='light' color='blue'>
                  {currency}
                </Badge>
              </Group>
              <NumberInput
                value={cost}
                onChange={handleCostChange}
                placeholder={t`0.00`}
                min={0}
                step={0.5}
                decimalScale={4}
                fixedDecimalScale={false}
                leftSection={<IconCurrencyDollar size='1rem' />}
                aria-label='unit-cost-input'
              />
              <Text size='10px' c='dimmed'>
                {t`Base acquisition or production cost`}
              </Text>
            </Stack>
          </Paper>

          {/* 2. Desired Margin Input */}
          <Paper p='xs' withBorder radius='sm'>
            <Stack gap='4px'>
              <Group justify='space-between'>
                <Text size='xs' fw={600} c='dimmed'>
                  {t`Desired Margin (%)`}
                </Text>
                <Badge
                  size='xs'
                  variant='light'
                  color='blue'
                >
                  {t`Target`}
                </Badge>
              </Group>
              <NumberInput
                value={margin}
                onChange={handleMarginChange}
                placeholder={t`e.g. 25.0`}
                min={-100}
                max={99.9}
                step={1}
                decimalScale={2}
                leftSection={<IconPercentage size='1rem' />}
                aria-label='desired-margin-input'
              />
              <Text size='10px' c='dimmed'>
                {t`Profit share of revenue: (Price - Cost) / Price`}
              </Text>
            </Stack>
          </Paper>

          {/* 3. Selling Price Input */}
          <Paper
            p='xs'
            withBorder
            radius='sm'
            style={{
              borderColor: 'var(--mantine-color-blue-4)',
              backgroundColor: 'rgba(34, 139, 230, 0.04)'
            }}
          >
            <Stack gap='4px'>
              <Group justify='space-between'>
                <Text size='xs' fw={700} c='blue'>
                  {t`Selling Price`}
                </Text>
                <Badge size='xs' variant='filled' color='blue'>
                  {currency}
                </Badge>
              </Group>
              <NumberInput
                value={sellingPrice}
                onChange={handlePriceChange}
                placeholder={t`0.00`}
                min={0}
                step={0.5}
                decimalScale={4}
                leftSection={<IconCurrencyDollar size='1rem' />}
                aria-label='selling-price-input'
              />
              <Text size='10px' c='dimmed'>
                {t`Standard selling price`}
              </Text>
            </Stack>
          </Paper>

          {/* 4. Minimum Price Floor Input */}
          <Paper
            p='xs'
            withBorder
            radius='sm'
            style={{
              borderColor: 'var(--mantine-color-blue-2)',
              backgroundColor: 'rgba(34, 139, 230, 0.02)'
            }}
          >
            <Stack gap='4px'>
              <Group justify='space-between'>
                <Text size='xs' fw={700} c='blue'>
                  {t`Minimum Price`}
                </Text>
                <Badge size='xs' variant='light' color='blue'>
                  {t`Floor`}
                </Badge>
              </Group>
              <NumberInput
                value={minPrice}
                onChange={(val) => setMinPrice(val ?? '')}
                placeholder={t`0.00`}
                min={0}
                step={0.5}
                decimalScale={4}
                leftSection={<IconCurrencyDollar size='1rem' />}
                aria-label='minimum-price-input'
              />
              <Text size='10px' c='dimmed'>
                {t`Sales orders cannot sell below this floor`}
              </Text>
            </Stack>
          </Paper>
        </SimpleGrid>

        {/* Quick Fill Cost Buttons (BOM / Purchase / Supplier) */}
        {(bomCost != null || purchaseCost != null || supplierCost != null) && (
          <Group gap='xs' wrap='wrap'>
            <Text size='xs' fw={600} c='dimmed'>
              {t`Quick-Set Cost:`}
            </Text>
            {bomCost != null && (
              <Button
                size='compact-xs'
                variant='light'
                color='blue'
                leftSection={<IconSparkles size='0.8rem' />}
                onClick={() => handleCostChange(bomCost)}
              >
                {t`Use BOM Cost`}: {formatCurrency(bomCost, { currency })}
              </Button>
            )}
            {purchaseCost != null && (
              <Button
                size='compact-xs'
                variant='light'
                color='blue'
                leftSection={<IconRefresh size='0.8rem' />}
                onClick={() => handleCostChange(purchaseCost)}
              >
                {t`Use Purchase Cost`}:{' '}
                {formatCurrency(purchaseCost, { currency })}
              </Button>
            )}
            {supplierCost != null && (
              <Button
                size='compact-xs'
                variant='light'
                color='blue'
                leftSection={<IconTrendingUp size='0.8rem' />}
                onClick={() => handleCostChange(supplierCost)}
              >
                {t`Use Supplier Cost`}:{' '}
                {formatCurrency(supplierCost, { currency })}
              </Button>
            )}
          </Group>
        )}

        {/* Live Metrics Summary Bar */}
        {metrics && (
          <Paper
            p='xs'
            radius='sm'
            withBorder
            style={{
              backgroundColor: 'rgba(34, 139, 230, 0.04)',
              borderColor: 'var(--mantine-color-blue-2)'
            }}
          >
            <Group justify='space-around' wrap='wrap' gap='md'>
              {/* Unit Profit */}
              <Group gap='xs'>
                <ThemeIcon
                  size='sm'
                  radius='xl'
                  color='blue'
                  variant='light'
                >
                  <IconCoins size='0.85rem' />
                </ThemeIcon>
                <Text size='xs' fw={600} c='dimmed'>
                  {t`Unit Profit:`}
                </Text>
                <Badge
                  color='blue'
                  variant='light'
                  size='md'
                  fw={700}
                >
                  {formatCurrency(metrics.profit, { currency })}
                </Badge>
              </Group>

              <Divider orientation='vertical' />

              {/* Gross Margin */}
              <Group gap='xs'>
                <ThemeIcon
                  size='sm'
                  radius='xl'
                  color='blue'
                  variant='light'
                >
                  <IconPercentage size='0.85rem' />
                </ThemeIcon>
                <Text size='xs' fw={600} c='dimmed'>
                  {t`Gross Margin:`}
                </Text>
                <Badge
                  color='blue'
                  variant='light'
                  size='md'
                  fw={700}
                >
                  {metrics.grossMargin.toFixed(1)}%
                </Badge>
              </Group>

              <Divider orientation='vertical' />

              {/* Cost Markup */}
              <Group gap='xs'>
                <ThemeIcon
                  size='sm'
                  radius='xl'
                  color='blue'
                  variant='light'
                >
                  <IconTrendingUp size='0.85rem' />
                </ThemeIcon>
                <Text size='xs' fw={600} c='dimmed'>
                  {t`Cost Markup:`}
                </Text>
                <Badge
                  color='blue'
                  variant='light'
                  size='md'
                  fw={700}
                >
                  {metrics.markup >= 0 ? `+${metrics.markup.toFixed(1)}%` : `${metrics.markup.toFixed(1)}%`}
                </Badge>
              </Group>
            </Group>
          </Paper>
        )}
      </Stack>
    </Card>
  );
}
