import { IconCalendar, IconUsers } from '@tabler/icons-react';
import { useMemo } from 'react';

import type { ApiFormFieldSet } from '@lib/types/Forms';
import { TagsField } from './CommonFields';

/**
 * Field set for creating / editing a NonConformance (NCR) report.
 */
export function useNonConformanceFields({
  partId
}: {
  partId?: number;
} = {}): ApiFormFieldSet {
  return useMemo(() => {
    const fields: ApiFormFieldSet = {
      reference: {},
      part: {
        disabled: !!partId,
        filters: { active: true }
      },
      title: {},
      description: {},
      severity: {},
      build_order: {},
      sales_order: {},
      purchase_order: {},
      return_order: {},
      quantity: {},
      root_cause: {},
      corrective_action: {},
      responsible: {
        icon: <IconUsers />,
        filters: { is_active: true }
      },
      target_date: {
        icon: <IconCalendar />
      },
      link: {},
      tags: TagsField({})
    };

    return fields;
  }, [partId]);
}

/**
 * Field set for the "set disposition" NCR transition action.
 */
export function useNonConformanceDispositionFields(): ApiFormFieldSet {
  return useMemo(() => {
    return {
      disposition: {}
    };
  }, []);
}

/**
 * Field set for linking a StockItem to a NonConformance (NCR) report.
 */
export function useNonConformanceStockItemFields({
  ncrId,
  partId
}: {
  ncrId?: number;
  partId?: number;
} = {}): ApiFormFieldSet {
  return useMemo(() => {
    return {
      ncr: {
        value: ncrId,
        hidden: true
      },
      stock_item: {
        filters: {
          part: partId,
          include_variants: false
        }
      },
      quantity: {},
      notes: {}
    };
  }, [ncrId, partId]);
}
