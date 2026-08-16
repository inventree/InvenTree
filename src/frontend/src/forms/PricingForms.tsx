import { t } from '@lingui/core/macro';
import { Alert } from '@mantine/core';
import { useMemo } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import { useCreateApiFormModal } from '../hooks/UseForm';
import { useGlobalSettingsState } from '../states/SettingsStates';

/**
 * Construct a set of fields for creating / updating a StockItemCost instance
 */
export function useStockItemCostFields(): ApiFormFieldSet {
  const globalSettings = useGlobalSettingsState();

  return useMemo(() => {
    const defaultCurrency = globalSettings.getSetting(
      'INVENTREE_DEFAULT_CURRENCY'
    );

    return {
      stock_item: {
        disabled: true
      },
      cost_type: {},
      min_cost: {},
      min_cost_currency: {
        default: defaultCurrency
      },
      max_cost: {},
      max_cost_currency: {
        default: defaultCurrency
      },
      notes: {}
    };
  }, [globalSettings]);
}

/**
 * Launch a form to create or update the cost data for a stock item.
 *
 * The 'pricing/cost/' endpoint upserts based on the (stock_item, cost_type)
 * pair, so a single create-style (POST) form serves both adding a new cost
 * entry and editing an existing one - just pass the existing entry as `cost`
 * to pre-populate the form.
 */
export function useStockItemCostForm({
  stockItem,
  cost,
  onFormSuccess
}: {
  stockItem: any;
  cost?: any;
  onFormSuccess?: (data: any) => void;
}) {
  const fields = useStockItemCostFields();

  return useCreateApiFormModal({
    url: ApiEndpoints.stock_item_cost_list,
    title: cost ? t`Edit Cost Entry` : t`Add Cost Entry`,
    preFormContent: (
      <Alert color='blue'>
        {t`Enter the cost per unit of stock - not the total cost for this stock item.`}
      </Alert>
    ),
    fields: fields,
    initialData: {
      stock_item: stockItem?.pk,
      cost_type: cost?.cost_type,
      min_cost: cost?.min_cost,
      min_cost_currency: cost?.min_cost_currency,
      max_cost: cost?.max_cost,
      max_cost_currency: cost?.max_cost_currency,
      notes: cost?.notes
    },
    onFormSuccess: onFormSuccess
  });
}
