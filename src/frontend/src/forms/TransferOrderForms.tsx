import type { ApiFormFieldSet } from '@lib/types/Forms';
import { t } from '@lingui/core/macro';
import { IconCalendar, IconUsers } from '@tabler/icons-react';
import { useMemo } from 'react';
import { useGlobalSettingsState } from '../states/SettingsStates';

export function useTransferOrderFields({
  duplicateOrderId
}: {
  duplicateOrderId?: number;
}): ApiFormFieldSet {
  const globalSettings = useGlobalSettingsState();

  return useMemo(() => {
    const fields: ApiFormFieldSet = {
      reference: {},
      description: {},
      project_code: {},
      start_date: {
        icon: <IconCalendar />
      },
      target_date: {
        icon: <IconCalendar />
      },
      take_from: {},
      destination: {
        filters: {
          structural: false
        }
      },
      consume: {},
      link: {},
      responsible: {
        filters: {
          is_active: true
        },
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
          copy_lines: {
            // Cannot duplicate lines from a transfer order!
            value: false,
            hidden: true
          },
          copy_extra_lines: {}
        }
      };
    }

    if (!globalSettings.isSet('PROJECT_CODES_ENABLED', true)) {
      delete fields.project_code;
    }

    return fields;
  }, [duplicateOrderId, globalSettings]);
}

export function useTransferOrderLineItemFields({
  orderId,
  create
}: {
  orderId?: number;
  create?: boolean;
}): ApiFormFieldSet {
  return useMemo(() => {
    const fields: ApiFormFieldSet = {
      order: {
        filters: {},
        disabled: true
      },
      part: {
        filters: {
          active: true
        }
        // onValueChange: (_: any, record?: any) => setPart(record)
      },
      reference: {},
      quantity: {
        // onValueChange: (value) => {
        //   setQuantity(value);
        // }
      },
      project_code: {
        description: t`Select project code for this line item`
      },
      target_date: {},
      notes: {},
      link: {}
    };

    return fields;
  }, [orderId, create]);
}
