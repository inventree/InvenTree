import { t } from '@lingui/core/macro';
import { useCallback, useMemo, useState } from 'react';

import type { ApiFormFieldSet } from '@lib/types/Forms';

/**
 * Return true if the provided cost entry specifies a range of costs (i.e. an estimate)
 */
export function isCostRange(entry: any): boolean {
  const min = entry?.min_cost;
  const max = entry?.max_cost;

  if (min === null || min === undefined || max === null || max === undefined) {
    return false;
  }

  return Number(min) !== Number(max);
}

/**
 * Field set for creating or editing a StockItemCostEntry.
 *
 * All costs are *per unit* of the stock item.
 * The "source" field is not shown - entries created via the UI are recorded as manual entries.
 *
 * An estimated cost is recorded as a cost range (minimum - maximum). The "estimate" checkbox
 * is not an API field - it controls whether the maximum cost is shown (and submitted):
 * - Not an estimate: a single "unit cost" is entered, and the maximum cost is submitted as null
 *   (so that the server sets it to the same value as the minimum cost)
 * - An estimate: separate minimum and maximum unit costs are entered
 *
 * An entry with different minimum and maximum costs is an estimate (see isCostRange).
 * When editing an existing entry, call setEstimate() with that entry *before* opening the form,
 * so that the form is constructed with the correct state (it is also re-checked against the
 * fetched data once the form loads).
 *
 * Returns:
 *  - fields: The form field set
 *  - processFormData: Pass to the form, to clear the maximum cost when not an estimate
 *  - setEstimate: Set the state of the "estimate" checkbox - false for a new entry,
 *    or isCostRange(entry) for an existing entry
 */
export function useStockItemCostEntryFields({
  stockItemId
}: {
  stockItemId: number;
}) {
  const [estimate, setEstimate] = useState<boolean>(false);

  const fields: ApiFormFieldSet = useMemo(() => {
    return {
      stock_item: {
        value: stockItemId,
        hidden: true
      },
      cost_type: {},
      currency: {},
      estimate: {
        field_type: 'boolean',
        exclude: true,
        label: t`Estimate`,
        description: t`This cost is an estimate - specify a range of costs`,
        value: estimate,
        // Note: When the form is reset to the fetched (API) values, this field has no value,
        // and the switch falls back to its default - which must match the current state
        default: estimate,
        onValueChange: (value: any, record?: any) => {
          if (record === undefined) {
            // Changed by the user
            setEstimate(!!value);
          } else {
            // Initial data fetched from the server (editing an existing entry)
            setEstimate(isCostRange(record));
          }
        }
      },
      min_cost: {
        label: estimate ? t`Minimum Unit Cost` : t`Unit Cost`,
        description: estimate
          ? t`Minimum cost per unit`
          : t`Cost per unit of the stock item`
      },
      max_cost: {
        hidden: !estimate,
        label: t`Maximum Unit Cost`,
        description: t`Maximum cost per unit`
      },
      notes: {}
    };
  }, [stockItemId, estimate]);

  const processFormData = useCallback(
    (data: any) => {
      if (!estimate) {
        // Not an estimate - the maximum cost is set to match the minimum cost
        data.max_cost = null;
      }

      return data;
    },
    [estimate]
  );

  return { fields, processFormData, setEstimate };
}
