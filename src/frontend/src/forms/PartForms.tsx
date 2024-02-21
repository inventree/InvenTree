import { t } from '@lingui/macro';
import { IconPackages } from '@tabler/icons-react';

import { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';

/**
 * Construct a set of fields for creating / editing a Part instance
 */
export function partFields({
  editing = false,
  category_id
}: {
  editing?: boolean;
  category_id?: number;
}): ApiFormFieldSet {
  let fields: ApiFormFieldSet = {
    category: {
      filters: {
        structural: false
      }
    },
    name: {},
    IPN: {},
    revision: {},
    description: {},
    variant_of: {},
    keywords: {},
    units: {},
    link: {},
    default_location: {
      filters: {
        structural: false
      }
    },
    default_expiry: {},
    minimum_stock: {},
    responsible: {
      filters: {
        is_active: true
      }
    },
    component: {},
    assembly: {},
    is_template: {},
    trackable: {},
    purchaseable: {},
    salable: {},
    virtual: {},
    active: {}
  };

  if (category_id != null) {
    // TODO: Set the value of the category field
  }

  // Additional fields for creation
  if (!editing) {
    // TODO: Hide 'active' field

    fields.copy_category_parameters = {};

    fields.initial_stock = {
      icon: <IconPackages />,
      children: {
        quantity: {},
        location: {}
      }
    };

    fields.initial_supplier = {
      children: {
        supplier: {
          filters: {
            is_supplier: true
          }
        },
        sku: {},
        manufacturer: {
          filters: {
            is_manufacturer: true
          }
        },
        mpn: {}
      }
    };
  }

  // TODO: pop 'expiry' field if expiry not enabled
  delete fields['default_expiry'];

  // TODO: pop 'revision' field if PART_ENABLE_REVISION is False
  delete fields['revision'];

  // TODO: handle part duplications

  return fields;
}

/**
 * Construct a set of fields for creating / editing a PartCategory instance
 */
export function partCategoryFields({}: {}): ApiFormFieldSet {
  let fields: ApiFormFieldSet = {
    parent: {
      description: t`Parent part category`,
      required: false
    },
    name: {},
    description: {},
    default_location: {
      filters: {
        structural: false
      }
    },
    default_keywords: {},
    structural: {},
    icon: {}
  };

  return fields;
}
