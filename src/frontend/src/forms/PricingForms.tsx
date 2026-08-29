import { t } from '@lingui/core/macro';
import { Alert } from '@mantine/core';
import { useMemo } from 'react';

import type { ApiFormFieldSet } from '@lib/types/Forms';
import { useGlobalSettingsState } from '../states/SettingsStates';

/**
 * Construct a set of fields for creating / updating a StockItemCostEntry instance
 */
export function useStockItemCostEntryFields(): ApiFormFieldSet {
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
 * Content displayed above the StockItemCostEntry create/edit form, clarifying
 * that each entry contributes towards the stock item's *unit* cost - not its
 * total value for the full quantity in stock.
 */
export function StockItemCostEntryFormAlert() {
  return (
    <Alert color='blue'>
      {t`Enter the cost per unit of stock - not the total cost for this stock item.`}
    </Alert>
  );
}
