import { t } from '@lingui/core/macro';
import { useMemo } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import type { ApiFormFieldSet } from '@lib/types/Forms';

/**
 * Construct a set of fields for creating / editing a TaxConfiguration instance
 */
export function taxConfigurationFields(): ApiFormFieldSet {
  return useMemo(() => {
    const fields: ApiFormFieldSet = {
      name: {
        field_type: 'string',
        required: true,
        description: t`Human-readable name for this tax configuration`
      },
      description: {
        field_type: 'string',
        description: t`Optional description of the tax configuration`
      },
      year: {
        field_type: 'integer',
        required: true,
        description: t`The year this tax configuration applies to`
      },
      rate: {
        field_type: 'decimal',
        required: true,
        description: t`Tax rate as a percentage (e.g., 10.00 for 10%)`
      },
      currency: {
        field_type: 'choice',
        required: true,
        description: t`Currency for this tax configuration`,
        api_url: apiUrl(ApiEndpoints.currency_list),
        pk_field: 'currency',
        modelRenderer: (instance: any) => instance.currency
      },
      is_active: {
        field_type: 'boolean',
        description: t`Whether this configuration is currently active`
      },
      is_inclusive: {
        field_type: 'boolean',
        description: t`Whether prices include tax (True) or exclude tax (False)`
      },
      applies_to_sales: {
        field_type: 'boolean',
        description: t`Whether this tax applies to sales orders`
      },
      applies_to_purchases: {
        field_type: 'boolean',
        description: t`Whether this tax applies to purchase orders`
      }
    };

    return fields;
  }, []);
}
