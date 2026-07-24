import { useMemo } from 'react';

import type { ApiFormFieldSet } from '@lib/types/Forms';

export function useRepairOrderFields({
  duplicateOrderId
}: {
  duplicateOrderId?: number;
}): ApiFormFieldSet {
  return useMemo(() => {
    const fields: ApiFormFieldSet = {
      reference: {},
      description: {},
      customer: {
        disabled: duplicateOrderId != undefined,
        filters: {
          is_customer: true,
          active: true
        }
      },
      asset: {
        filters: {
          is_building: false
        }
      },
      symptoms: {}
    };

    // Order duplication fields
    if (!!duplicateOrderId) {
      fields.duplicate = {
        children: {
          order_id: {
            hidden: true,
            value: duplicateOrderId
          },
          copy_lines: {
            value: true
          }
        }
      };
    }

    return fields;
  }, [duplicateOrderId]);
}

export function useRepairOrderLineItemFields({
  orderId,
  create
}: {
  orderId: number;
  create?: boolean;
}) {
  return useMemo(() => {
    return {
      order: {
        disabled: true,
        value: orderId
      },
      part: {
        filters: {
          active: true
        }
      },
      quantity: {}
    };
  }, [create, orderId]);
}
