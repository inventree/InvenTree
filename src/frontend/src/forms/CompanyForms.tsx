import { t } from '@lingui/macro';
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
import { useEffect, useMemo, useState } from 'react';

import { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { openEditApiForm } from '../functions/forms';

/**
 * Field set for SupplierPart instance
 */
export function useSupplierPartFields({
  partPk,
  supplierPk,
  hidePart
}: {
  partPk?: number;
  supplierPk?: number;
  hidePart?: boolean;
}) {
  const [part, setPart] = useState<number | undefined>(partPk);

  useEffect(() => {
    setPart(partPk);
  }, [partPk]);

  return useMemo(() => {
    const fields: ApiFormFieldSet = {
      part: {
        hidden: hidePart,
        value: part,
        onValueChange: setPart,
        filters: {
          purchaseable: true
        }
      },
      manufacturer_part: {
        filters: {
          part_detail: true,
          manufacturer_detail: true
        },
        adjustFilters: (filters: any) => {
          if (part) {
            filters.part = part;
          }

          return filters;
        }
      },
      supplier: {},
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
      }
    };

    if (supplierPk !== undefined) {
      fields.supplier.value = supplierPk;
    }

    return fields;
  }, [part]);
}

export function useManufacturerPartFields() {
  return useMemo(() => {
    const fields: ApiFormFieldSet = {
      part: {},
      manufacturer: {},
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
    is_customer: {}
  };
}
