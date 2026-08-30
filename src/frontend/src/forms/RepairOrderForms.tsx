import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { t } from '@lingui/core/macro';
import { IconCalendar, IconLink, IconUsers } from '@tabler/icons-react';
import { useMemo } from 'react';

import type { ApiFormFieldSet } from '@lib/types/Forms';
import { useCreateApiFormModal } from '../hooks/UseForm';

export function useRepairOrderFields({
  duplicateOrderId
}: {
  duplicateOrderId?: number;
}): ApiFormFieldSet {
  return useMemo(() => {
    const fields: ApiFormFieldSet = {
      reference: {},
      description: {},
      part: {
        filters: {
          assembly: true,
          active: true
        }
      },
      symptoms: {},
      customer: {
        disabled: duplicateOrderId != undefined,
        filters: {
          is_customer: true,
          active: true
        }
      },
      start_date: {
        icon: <IconCalendar />
      },
      target_date: {
        icon: <IconCalendar />
      },
      responsible: {
        filters: {
          is_active: true
        },
        icon: <IconUsers />
      },
      link: {
        icon: <IconLink />
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
  assemblyPartId,
  create
}: {
  orderId: number;
  assemblyPartId?: number;
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
          active: true,
          in_bom_for: assemblyPartId || undefined
        }
      },
      quantity: {}
    };
  }, [create, orderId, assemblyPartId]);
}

export function useRepairOrderAutoAllocateFields(): ApiFormFieldSet {
  return useMemo(() => {
    return {
      location: {},
      exclude_location: {},
      stock_sort_by: {}
    };
  }, []);
}

export function useAllocateStockToRepairOrderForm({
  lineItem,
  onFormSuccess
}: {
  lineItem: any;
  onFormSuccess: () => void;
}) {
  const fields: ApiFormFieldSet = useMemo(() => {
    const outstanding = Math.max(
      (lineItem?.quantity ?? 0) - (lineItem?.allocated ?? 0),
      0
    );

    return {
      line: {
        hidden: true,
        value: lineItem?.pk
      },
      item: {
        filters: {
          part: lineItem?.part,
          available: true,
          part_detail: true,
          location_detail: true
        }
      },
      quantity: {
        value: outstanding
      }
    };
  }, [lineItem]);

  return useCreateApiFormModal({
    url: ApiEndpoints.repair_order_allocation_list,
    title: t`Allocate Stock`,
    fields: fields,
    onFormSuccess: onFormSuccess,
    successMessage: t`Stock allocated`
  });
}
