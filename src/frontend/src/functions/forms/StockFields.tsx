import { t } from '@lingui/macro';

import {
  ApiFormFieldSet,
  ApiFormFieldType
} from '../../components/forms/fields/ApiFormField';

/**
 * Construct a set of fields for creating / editing a StockItem instance
 */
export function stockFields({}: {}): ApiFormFieldSet {
  let fields: ApiFormFieldSet = {
    part: {
      onValueChange: (value: any) => {
        // TODO: implement this
        console.log('part changed: ', value);
      }
    },
    supplier_part: {
      // TODO: icon
      // TODO: implement adjustFilters
      filters: {
        part_detail: true,
        supplier_detail: true
      }
    },
    use_pack_size: {
      description: t`Add given quantity as packs instead of individual items`
    },
    location: {
      filters: {
        structural: false
      }
      // TODO: icon
    },
    quantity: {
      description: t`Enter initial quantity for this stock item`
    },
    serial_numbers: {
      // TODO: icon
      fieldType: 'string',
      label: t`Serial Numbers`,
      description: t`Enter serial numbers for new stock (or leave blank)`,
      required: false
    },
    serial: {
      // TODO: icon
    },
    batch: {
      // TODO: icon
    },
    status: {},
    expiry_date: {
      // TODO: icon
    },
    purchase_price: {
      // TODO: icon
    },
    purchase_price_currency: {
      // TODO: icon
    },
    packaging: {
      // TODO: icon,
    },
    link: {
      // TODO: icon
    },
    owner: {
      // TODO: icon
    },
    delete_on_deplete: {}
  };

  // TODO: Handle custom field management based on provided options
  // TODO: refer to stock.py in original codebase

  return fields;
}
