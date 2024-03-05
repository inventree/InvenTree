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
import { useEffect, useMemo, useState } from 'react';

import {
  ApiFormAdjustFilterType,
  ApiFormFieldSet
} from '../components/forms/fields/ApiFormField';

/*
 * Construct a set of fields for creating / editing a PurchaseOrderLineItem instance
 */
export function usePurchaseOrderLineItemFields({
  create
}: {
  create?: boolean;
}) {
  const [purchasePrice, setPurchasePrice] = useState<string>('');
  const [autoPricing, setAutoPricing] = useState(true);

  useEffect(() => {
    if (autoPricing) {
      setPurchasePrice('');
    }
  }, [autoPricing]);

  useEffect(() => {
    setAutoPricing(purchasePrice === '');
  }, [purchasePrice]);

  const fields = useMemo(() => {
    const fields: ApiFormFieldSet = {
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
        icon: <IconCurrencyDollar />,
        value: purchasePrice,
        onValueChange: setPurchasePrice
      },
      purchase_price_currency: {
        icon: <IconCoins />
      },
      auto_pricing: {
        value: autoPricing,
        onValueChange: setAutoPricing
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

    if (create) {
      fields['merge_items'] = {};
    }

    return fields;
  }, [create, autoPricing, purchasePrice]);

  return fields;
}

/**
 * Construct a set of fields for creating / editing a PurchaseOrder instance
 */
export function purchaseOrderFields(): ApiFormFieldSet {
  return {
    reference: {
      icon: <IconHash />
    },
    description: {},
    supplier: {
      filters: {
        is_supplier: true
      }
    },
    supplier_reference: {},
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
