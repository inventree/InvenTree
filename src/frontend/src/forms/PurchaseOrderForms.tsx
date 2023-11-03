import {
  IconCalendar,
  IconCoins,
  IconCurrencyDollar,
  IconLink,
  IconNotes,
  IconSitemap
} from '@tabler/icons-react';

import { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';

/*
 * Construct a set of fields for creating / editing a PurchaseOrderLineItem instance
 */
export function purchaseOrderLineItemFields({
  supplierId
}: {
  supplierId?: number;
}) {
  let fields: ApiFormFieldSet = {
    order: {
      filters: {
        supplier_detail: true
      }
    },
    part: {
      filters: {
        part_detail: true,
        supplier_detail: true,
        supplier: supplierId
      }
      // TODO: Custom onEdit callback (see purchase_order.js)
      // TODO: secondary modal (see purchase_order.js)
    },
    quantity: {},
    reference: {},
    purchase_price: {
      icon: <IconCurrencyDollar />
    },
    purchase_price_currency: {
      icon: <IconCoins />
    },
    target_date: {
      icon: <IconCalendar />
    },
    destination: {
      icon: <IconSitemap />
    },
    notes: {
      icon: <IconNotes />
    },
    link: {
      icon: <IconLink />
    }
  };

  return fields;
}
