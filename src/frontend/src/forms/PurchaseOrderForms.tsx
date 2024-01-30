import {
  IconAddressBook,
  IconCalendar,
  IconCoins,
  IconCurrencyDollar,
  IconHash,
  IconLink,
  IconList,
  IconNotes,
  IconSitemap,
  IconUser,
  IconUsers
} from '@tabler/icons-react';

import {
  ApiFormAdjustFilterType,
  ApiFormFieldSet
} from '../components/forms/fields/ApiFormField';

/*
 * Construct a set of fields for creating / editing a PurchaseOrderLineItem instance
 */
export function purchaseOrderLineItemFields() {
  let fields: ApiFormFieldSet = {
    order: {
      filters: {
        supplier_detail: true
      },
      hidden: true
    },
    part: {
      filters: {
        part_detail: true,
        supplier_detail: true
      },
      adjustFilters: (value: ApiFormAdjustFilterType) => {
        // TODO: Adjust part based on the supplier associated with the supplier
        return value.filters;
      }
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

/**
 * Construct a set of fields for creating / editing a PurchaseOrder instance
 */
export function PurchaseOrderFormFields(): ApiFormFieldSet {
  return {
    reference: {
      icon: <IconHash />
    },
    supplier: {
      filters: {
        is_supplier: true
      }
    },
    supplier_reference: {},
    description: {},
    project_code: {
      icon: <IconList />
    },
    order_currency: {
      icon: <IconCoins />
    },
    target_date: {
      icon: <IconCalendar />
    },
    link: {},
    contact: {
      icon: <IconUser />,
      filters: {
        supplier_detail: true
      },
      adjustFilters: (value: ApiFormAdjustFilterType) => {
        return {
          ...value.filters,
          company: value.data.supplier
        };
      }
    },
    address: {
      icon: <IconAddressBook />,
      adjustFilters: (value: ApiFormAdjustFilterType) => {
        return {
          ...value.filters,
          company: value.data.supplier
        };
      }
    },
    responsible: {
      icon: <IconUsers />
    }
  };
}
