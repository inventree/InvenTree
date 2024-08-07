import { IconAddressBook, IconUser, IconUsers } from '@tabler/icons-react';
import { useMemo } from 'react';

import {
  ApiFormAdjustFilterType,
  ApiFormFieldSet
} from '../components/forms/fields/ApiFormField';

export function useSalesOrderFields(): ApiFormFieldSet {
  return useMemo(() => {
    return {
      reference: {},
      description: {},
      customer: {
        filters: {
          is_customer: true,
          active: true
        }
      },
      customer_reference: {},
      project_code: {},
      order_currency: {},
      target_date: {},
      link: {},
      contact: {
        icon: <IconUser />,
        adjustFilters: (value: ApiFormAdjustFilterType) => {
          return {
            ...value.filters,
            company: value.data.customer
          };
        }
      },
      address: {
        icon: <IconAddressBook />,
        adjustFilters: (value: ApiFormAdjustFilterType) => {
          return {
            ...value.filters,
            company: value.data.customer
          };
        }
      },
      responsible: {
        icon: <IconUsers />
      }
    };
  }, []);
}

export function useSalesOrderLineItemFields({
  customerId,
  orderId,
  create
}: {
  customerId?: number;
  orderId?: number;
  create?: boolean;
}): ApiFormFieldSet {
  const fields = useMemo(() => {
    return {
      order: {
        filters: {
          customer_detail: true
        },
        disabled: true,
        value: create ? orderId : undefined
      },
      part: {
        filters: {
          active: true,
          salable: true
        }
      },
      reference: {},
      quantity: {},
      sale_price: {},
      sale_price_currency: {},
      target_date: {},
      notes: {},
      link: {}
    };
  }, []);

  return fields;
}

export function useSalesOrderShipmentFields(): ApiFormFieldSet {
  return useMemo(() => {
    return {
      order: {
        disabled: true
      },
      reference: {},
      shipment_date: {},
      delivery_date: {},
      tracking_number: {},
      invoice_number: {},
      link: {},
      notes: {}
    };
  }, []);
}

export function useReturnOrderFields(): ApiFormFieldSet {
  return useMemo(() => {
    return {
      reference: {},
      description: {},
      customer: {
        filters: {
          is_customer: true,
          active: true
        }
      },
      customer_reference: {},
      project_code: {},
      order_currency: {},
      target_date: {},
      link: {},
      contact: {
        icon: <IconUser />,
        adjustFilters: (value: ApiFormAdjustFilterType) => {
          return {
            ...value.filters,
            company: value.data.customer
          };
        }
      },
      address: {
        icon: <IconAddressBook />,
        adjustFilters: (value: ApiFormAdjustFilterType) => {
          return {
            ...value.filters,
            company: value.data.customer
          };
        }
      },
      responsible: {
        filters: {
          is_active: true
        },
        icon: <IconUsers />
      }
    };
  }, []);
}
