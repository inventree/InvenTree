import { t } from '@lingui/macro';

import {
  ApiFormChangeCallback,
  ApiFormData,
  ApiFormFieldSet
} from '../../components/forms/fields/ApiFormField';
import { ApiPaths } from '../../states/ApiState';
import { openCreateApiForm, openEditApiForm } from '../forms';

/**
 * Construct a set of fields for creating / editing a StockItem instance
 */
export function stockFields({}: {}): ApiFormFieldSet {
  let fields: ApiFormFieldSet = {
    part: {
      onValueChange: (change: ApiFormChangeCallback) => {
        // TODO: implement remaining functionality from old stock.py
        console.log('part changed: ', change.value);

        // Clear the 'supplier_part' field if the part is changed
        change.form.setValues({
          supplier_part: null
        });
      }
    },
    supplier_part: {
      // TODO: icon
      // TODO: implement adjustFilters
      filters: {
        part_detail: true,
        supplier_detail: true
      },
      adjustFilters: (filters: any, form: ApiFormData) => {
        let part = form.values.part;
        if (part) {
          filters.part = part;
        }

        return filters;
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
      field_type: 'string',
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

/**
 * Launch a form to create a new StockItem instance
 */
export function createStockItem() {
  openCreateApiForm({
    name: 'stockitem-create',
    url: ApiPaths.stock_item_list,
    fields: stockFields({}),
    title: t`Create Stock Item`
  });
}

/**
 * Launch a form to edit an existing StockItem instance
 * @param item : primary key of the StockItem to edit
 */
export function editStockItem(item: number) {
  openEditApiForm({
    name: 'stockitem-edit',
    url: ApiPaths.stock_item_list,
    pk: item,
    fields: stockFields({}),
    title: t`Edit Stock Item`
  });
}
