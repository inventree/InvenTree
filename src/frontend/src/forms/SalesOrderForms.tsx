import { IconAddressBook, IconUser, IconUsers } from '@tabler/icons-react';
import { useMemo } from 'react';

import {
  ApiFormAdjustFilterType,
  ApiFormFieldSet
} from '../components/forms/fields/ApiFormField';

export function useSalesOrderFields({
  duplicateOrderId
}: {
  duplicateOrderId?: number;
}): ApiFormFieldSet {
  return useMemo(() => {
    let fields: ApiFormFieldSet = {
      reference: {},
      description: {},
      customer: {
        disabled: duplicateOrderId != undefined,
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

    // Order duplication fields
    if (!!duplicateOrderId) {
      fields.duplicate = {
        children: {
          order_id: {
            hidden: true,
            value: duplicateOrderId
          },
          copy_lines: {},
          copy_extra_lines: {}
        }
      };
    }

    return fields;
  }, [duplicateOrderId]);
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

export function useSalesOrderAllocateSerialsFields({
  itemId,
  orderId
}: {
  itemId: number;
  orderId: number;
}): ApiFormFieldSet {
  return useMemo(() => {
    return {
      line_item: {
        value: itemId,
        hidden: true
      },
      quantity: {},
      serial_numbers: {},
      shipment: {
        filters: {
          order_detail: true,
          order: orderId,
          shipped: false
        }
      }
    };
  }, [itemId, orderId]);
}

export function useSalesOrderShipmentFields({
  pending
}: {
  pending?: boolean;
}): ApiFormFieldSet {
  return useMemo(() => {
    return {
      order: {
        disabled: true
      },
      reference: {},
      shipment_date: {
        hidden: pending ?? true
      },
      delivery_date: {
        hidden: pending ?? true
      },
      tracking_number: {},
      invoice_number: {},
      link: {}
    };
  }, [pending]);
}

export function useSalesOrderShipmentCompleteFields({
  shipmentId
}: {
  shipmentId?: number;
}): ApiFormFieldSet {
  return useMemo(() => {
    return {
      shipment_date: {},
      tracking_number: {},
      invoice_number: {},
      link: {}
    };
  }, [shipmentId]);
}

export function useSalesOrderAllocationFields({
  shipmentId
}: {
  shipmentId?: number;
}): ApiFormFieldSet {
  return useMemo(() => {
    return {
      quantity: {}
    };
  }, [shipmentId]);
}
