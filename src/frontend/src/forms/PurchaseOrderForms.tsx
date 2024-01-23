import {
  IconAddressBook,
  IconCalendar,
  IconCoins,
  IconCurrencyDollar,
  IconHash,
  IconLink,
  IconNotes,
  IconSitemap,
  IconUser
} from '@tabler/icons-react';
import { useEffect, useMemo, useState } from 'react';

import { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';

/*
 * Construct a set of fields for creating / editing a PurchaseOrderLineItem instance
 */
export function purchaseOrderLineItemFields({
  supplierId,
  orderId,
  create = false
}: {
  supplierId?: number;
  orderId?: number;
  create?: boolean;
}) {
  let fields: ApiFormFieldSet = {
    order: {
      filters: {
        supplier_detail: true
      },
      value: orderId,
      hidden: create != true || orderId != undefined
    },
    part: {
      filters: {
        part_detail: true,
        supplier_detail: true,
        supplier: supplierId
      },
      adjustFilters: (filters: any) => {
        // TODO: Filter by the supplier associated with the order
        return filters;
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

/*
 * Field set for a PurchaseOrder instance
 */
export function usePurchaseOrderFields({
  supplierId
}: {
  supplierId?: number;
}) {
  const [supplier, setSupplier] = useState<number | undefined>(supplierId);

  // Set initial value for Supplier ID
  useEffect(() => {
    setSupplier(supplierId);
  }, [supplierId]);

  const fields = useMemo(() => {
    const fieldsset: ApiFormFieldSet = {
      reference: {
        icon: <IconHash />
      },
      description: {},
      supplier: {
        value: supplier,
        onValueChange: setSupplier,
        filters: {
          is_supplier: true
        }
      },
      supplier_reference: {},
      project_code: {},
      order_currency: {},
      target_date: {
        icon: <IconCalendar />
      },
      link: {
        icon: <IconLink />
      },
      contact: {
        adjustFilters: (filters: any) => {
          if (supplier !== undefined) {
            filters.company = supplier;
          }

          return filters;
        },
        icon: <IconUser />
      },
      address: {
        icon: <IconAddressBook />
      },
      responsible: {}
    };

    return fieldsset;
  }, [supplier]);

  return fields;
}
