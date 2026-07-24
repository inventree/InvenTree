import type {
  ApiFormAdjustFilterType,
  ApiFormFieldSet
} from '@lib/types/Forms';
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
import { useMemo, useState } from 'react';
import { DuplicateField, TagsField } from './CommonFields';

/**
 * Field set for SupplierPart instance
 */
export function useSupplierPartFields({
  manufacturerId,
  manufacturerPartId,
  partId,
  duplicateSupplierPartId
}: {
  manufacturerId?: number;
  manufacturerPartId?: number;
  partId?: number;
  duplicateSupplierPartId?: number | null;
}) {
  const [part, setPart] = useState<any>({});

  return useMemo(() => {
    const fields: ApiFormFieldSet = {
      part: {
        value: partId,
        disabled: !!partId,
        filters: {
          part: partId,
          purchaseable: true,
          active: true
        },
        onValueChange: (value: any, record: any) => {
          setPart(record);
        }
      },
      manufacturer_part: {
        value: manufacturerPartId,
        autoFill: true,
        filters: {
          manufacturer: manufacturerId,
          part_detail: true,
          manufacturer_detail: true
        },
        adjustFilters: (adjust: ApiFormAdjustFilterType) => {
          return {
            ...adjust.filters,
            part: adjust.data.part
          };
        },
        addCreateFields: {
          part: {
            value: part?.pk,
            disabled: !!part?.pk
          },
          manufacturer: {},
          MPN: {},
          description: {},
          link: {}
        }
      },
      supplier: {
        filters: {
          active: true,
          is_supplier: true
        },
        addCreateFields: {
          name: {},
          description: {},
          is_supplier: { value: true, hidden: true }
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
      primary: {},
      active: {},
      duplicate: DuplicateField({
        originalId: duplicateSupplierPartId,
        extraFields: {
          copy_parameters: {}
        }
      })
    };

    if (!duplicateSupplierPartId) {
      delete fields.duplicate;
    }

    return fields;
  }, [
    manufacturerId,
    manufacturerPartId,
    partId,
    part,
    duplicateSupplierPartId
  ]);
}

export function useManufacturerPartFields({
  duplicateManufacturerPartId
}: {
  duplicateManufacturerPartId?: number | null;
} = {}) {
  return useMemo(() => {
    const fields: ApiFormFieldSet = {
      part: {},
      manufacturer: {
        filters: {
          active: true,
          is_manufacturer: true
        },
        addCreateFields: {
          name: {},
          description: {},
          is_manufacturer: { value: true, hidden: true }
        }
      },
      MPN: {},
      description: {},
      tags: TagsField({}),
      link: {},
      duplicate: DuplicateField({
        originalId: duplicateManufacturerPartId,
        extraFields: {
          copy_parameters: {}
        }
      })
    };

    if (!duplicateManufacturerPartId) {
      delete fields.duplicate;
    }

    return fields;
  }, [duplicateManufacturerPartId]);
}

/**
 * Field set for editing a company instance
 */
export function companyFields({
  duplicateCompanyId
}: {
  duplicateCompanyId?: number | null;
} = {}): ApiFormFieldSet {
  const fields: ApiFormFieldSet = {
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
    tax_id: {},
    is_supplier: {},
    is_manufacturer: {},
    is_customer: {},
    active: {},
    duplicate: DuplicateField({
      originalId: duplicateCompanyId,
      extraFields: {
        copy_parameters: {}
      }
    })
  };

  if (!duplicateCompanyId) {
    delete fields.duplicate;
  }

  return fields;
}
