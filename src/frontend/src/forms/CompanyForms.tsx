import {
  IconAt,
  IconCurrencyDollar,
  IconGlobe,
  IconHash,
  IconLink,
  IconNote,
  IconPackage,
  IconPhone
} from '@tabler/icons-react';
import { useMemo } from 'react';

import type {
  ApiFormAdjustFilterType,
  ApiFormFieldSet
} from '../components/forms/fields/ApiFormField';

/**
 * Field set for SupplierPart instance
 */
export function useSupplierPartFields({
  partId
}: {
  partId?: number;
}) {
  return useMemo(() => {
    const fields: ApiFormFieldSet = {
      part: {
        value: partId,
        disabled: !!partId,
        filters: {
          part: partId,
          purchaseable: true,
          active: true
        }
      },
      manufacturer_part: {
        filters: {
          part_detail: true,
          manufacturer_detail: true
        },
        adjustFilters: (adjust: ApiFormAdjustFilterType) => {
          return {
            ...adjust.filters,
            part: adjust.data.part
          };
        }
      },
      supplier: {
        filters: {
          active: true,
          is_supplier: true
        }
      },
      SKU: {
        icon: <IconHash />
      },
      description: {},
      link: {
        icon: <IconLink />
      },
      note: {
        icon: <IconNote />
      },
      pack_quantity: {},
      packaging: {
        icon: <IconPackage />
      },
      active: {}
    };

    return fields;
  }, [partId]);
}

export function useManufacturerPartFields() {
  return useMemo(() => {
    const fields: ApiFormFieldSet = {
      part: {},
      manufacturer: {
        filters: {
          active: true,
          is_manufacturer: true
        }
      },
      MPN: {},
      description: {},
      link: {}
    };

    return fields;
  }, []);
}

export function useManufacturerPartParameterFields() {
  return useMemo(() => {
    const fields: ApiFormFieldSet = {
      manufacturer_part: {
        disabled: true
      },
      name: {},
      value: {},
      units: {}
    };

    return fields;
  }, []);
}

/**
 * Field set for editing a company instance
 */
export function companyFields(): ApiFormFieldSet {
  return {
    name: {},
    description: {},
    website: {
      icon: <IconGlobe />
    },
    currency: {
      icon: <IconCurrencyDollar />
    },
    phone: {
      icon: <IconPhone />
    },
    email: {
      icon: <IconAt />
    },
    is_supplier: {},
    is_manufacturer: {},
    is_customer: {},
    active: {}
  };
}
