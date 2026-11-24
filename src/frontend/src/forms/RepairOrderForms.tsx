import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { t } from '@lingui/core/macro';
import { IconCalendar, IconLink, IconUsers } from '@tabler/icons-react';
import { useMemo } from 'react';

import type { ApiFormFieldSet } from '@lib/types/Forms';
import { useCreateApiFormModal } from '../hooks/UseForm';
import { useGlobalSettingsState } from '../states/SettingsStates';
import { ProjectCodeField, TagsField } from './CommonFields';

export function useRepairOrderFields({
  duplicateOrderId
}: {
  duplicateOrderId?: number;
}): ApiFormFieldSet {
  const globalSettings = useGlobalSettingsState();

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
      project_code: ProjectCodeField(),
      priority: {},
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
      take_from: {},
      responsible: {
        filters: {
          is_active: true
        },
        icon: <IconUsers />
      },
      link: {
        icon: <IconLink />
      },
      tags: TagsField({})
    };

    if (!globalSettings.isSet('PROJECT_CODES_ENABLED', true)) {
      delete fields.project_code;
    }

    // Order duplication fields
    if (!!duplicateOrderId) {
      fields.duplicate = {
        children: {
          original: {
            hidden: true,
            value: duplicateOrderId
          },
          copy_lines: {},
          copy_parameters: {},
          copy_notes: {}
        }
      };
    }

    return fields;
  }, [duplicateOrderId, globalSettings]);
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

export function useRepairOrderAutoAllocateFields({
  sourceLocation
}: {
  sourceLocation?: number | null;
}): ApiFormFieldSet {
  return useMemo(() => {
    return {
      location: {
        value: sourceLocation ?? undefined
      },
      exclude_location: {},
      stock_sort_by: {}
    };
  }, [sourceLocation]);
}

export function useAllocateStockToRepairOrderForm({
  lineItem,
  sourceLocation,
  onFormSuccess
}: {
  lineItem: any;
  sourceLocation?: number | null;
  onFormSuccess: () => void;
}) {
  const fields: ApiFormFieldSet = useMemo(() => {
    const outstanding = Math.max(
      (lineItem?.quantity ?? 0) -
        (lineItem?.allocated ?? 0) -
        (lineItem?.consumed ?? 0),
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
          location_detail: true,
          location: sourceLocation ?? undefined,
          cascade: sourceLocation ? true : undefined
        }
      },
      quantity: {
        value: outstanding
      }
    };
  }, [lineItem, sourceLocation]);

  return useCreateApiFormModal({
    url: ApiEndpoints.repair_order_allocation_list,
    title: t`Allocate Stock`,
    fields: fields,
    onFormSuccess: onFormSuccess,
    successMessage: t`Stock allocated`
  });
}
