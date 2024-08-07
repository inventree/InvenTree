import { IconUsers } from '@tabler/icons-react';
import { useMemo } from 'react';

export function useReturnOrderLineItemFields({
  orderId,
  customerId,
  create
}: {
  orderId: number;
  customerId: number;
  create?: boolean;
}) {
  return useMemo(() => {
    return {
      order: {
        disabled: true,
        filters: {
          customer_detail: true
        }
      },
      item: {
        filters: {
          customer: customerId,
          part_detail: true,
          serialized: true
        }
      },
      reference: {},
      outcome: {
        hidden: create == true
      },
      price: {},
      price_currency: {},
      target_date: {},
      notes: {},
      link: {},
      responsible: {
        filters: {
          is_active: true
        },
        icon: <IconUsers />
      }
    };
  }, [create, orderId, customerId]);
}
