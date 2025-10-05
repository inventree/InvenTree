import { t } from '@lingui/core/macro';
import { useMemo } from 'react';

import type { ApiFormFieldSet } from '@lib/types/Forms';

/**
 * Construct a set of fields for creating / editing a Tenant instance
 */
export function tenantFields(): ApiFormFieldSet {
  return useMemo(() => {
    const fields: ApiFormFieldSet = {
      name: {
        field_type: 'string',
        required: true,
        description: t`Unique name for the tenant`
      },
      description: {
        field_type: 'string',
        description: t`Optional description of the tenant`
      },
      code: {
        field_type: 'string',
        description: t`Optional unique code/identifier for the tenant`
      },
      is_active: {
        field_type: 'boolean',
        description: t`Whether this tenant is currently active`
      },
      contact_name: {
        field_type: 'string',
        description: t`Optional contact person name`
      },
      contact_email: {
        field_type: 'string',
        description: t`Optional contact email`
      },
      contact_phone: {
        field_type: 'string',
        description: t`Optional contact phone number`
      }
    };

    return fields;
  }, []);
}
