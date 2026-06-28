import { ApiEndpoints, ModelType, ProgressBar, apiUrl } from '@lib/index';
import type { ApiFormFieldSet, ApiFormFieldType } from '@lib/types/Forms';
import { t } from '@lingui/core/macro';
import { NumberInput, Table } from '@mantine/core';
import { IconCalendar, IconUsers } from '@tabler/icons-react';
import { useMemo, useState } from 'react';
import RemoveRowButton from '../components/buttons/RemoveRowButton';
import { StandaloneField } from '../components/forms/StandaloneField';
import type { TableFieldRowProps } from '../components/forms/fields/TableField';
import { useWhyDidYouUpdate } from '../functions/debug';
import { useCreateApiFormModal } from '../hooks/UseForm';
import { useGlobalSettingsState } from '../states/SettingsStates';
import { RenderPartColumn } from '../tables/ColumnRenderers';
import { ProjectCodeField, TagsField } from './CommonFields';

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
      project_code: ProjectCodeField(),
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
      tags: TagsField({}),
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
          copy_lines: {},
          // Transfer Orders don't have extra lines for now...
          copy_extra_lines: { hidden: true, value: false }
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
          active: true,
          virtual: false
        }
      },
      reference: {},
      quantity: {},
      project_code: ProjectCodeField(),
      target_date: {},
      notes: {},
      link: {}
    };

    return fields;
  }, [orderId, create]);
}

function TransferOrderAllocateLineRow({
  props,
  record,
  sourceLocation
}: Readonly<{
  props: TableFieldRowProps;
  record: any;
  sourceLocation?: number | null;
}>) {
  useWhyDidYouUpdate('TransferOrderAllocateLineRow', {
    props,
    record,
    sourceLocation
  });

  const [quantity, setQuantity] = useState<number | ''>(
    props.item?.quantity ?? ''
  );

  // Statically defined field for selecting the stock item
  const stockItemField: ApiFormFieldType = useMemo(() => {
    return {
      field_type: 'related field',
      api_url: apiUrl(ApiEndpoints.stock_item_list),
      model: ModelType.stockitem,
      autoFill: true,
      filters: {
        available: true,
        part_detail: true,
        location_detail: true,
        location: sourceLocation,
        cascade: sourceLocation ? true : undefined,
        part: record.part
      },
      value: props.item.stock_item,
      name: 'stock_item',
      onValueChange: (value: any, instance: any) => {
        props.changeFn(props.rowId, 'stock_item', value);

        // Update the allocated quantity based on the selected stock item
        if (instance) {
          const available = instance.quantity - instance.allocated;
          const required = record.quantity - record.allocated;

          let q = props.item?.quantity ?? 0;

          q = Math.max(q, required);
          q = Math.min(q, available);

          if (q != quantity) {
            setQuantity(q);
            props.changeFn(props.rowId, 'quantity', q);
          }
        }
      }
    };
  }, [sourceLocation, record, quantity]);

  return (
    <Table.Tr key={`table-row-${props.rowId}`}>
      <Table.Td>
        <RenderPartColumn part={record.part_detail} />
      </Table.Td>
      <Table.Td>
        <ProgressBar
          value={record.allocated}
          maximum={record.quantity}
          progressLabel
        />
      </Table.Td>
      <Table.Td>
        <StandaloneField
          fieldName='stock_item'
          fieldDefinition={stockItemField}
          error={props.rowErrors?.stock_item?.message}
        />
      </Table.Td>
      <Table.Td>
        <NumberInput
          radius='sm'
          min={0}
          step={1}
          decimalScale={10}
          value={quantity}
          onChange={(value: number | string) => {
            let nextValue: number | '' = '';

            if (typeof value === 'number') {
              nextValue = Number.isFinite(value) ? value : '';
            } else if (value.trim() !== '') {
              const parsed = Number.parseFloat(value);
              nextValue = Number.isFinite(parsed) ? parsed : '';
            }

            setQuantity(nextValue);
            props.changeFn(props.rowId, 'quantity', nextValue);
          }}
          error={props.rowErrors?.quantity?.message}
        />
      </Table.Td>
      <Table.Td>
        <RemoveRowButton onClick={() => props.removeFn(props.rowId)} />
      </Table.Td>
    </Table.Tr>
  );
}

export function useAllocateToTransferOrderForm({
  orderId,
  sourceLocationId,
  lineItems,
  onFormSuccess
}: {
  orderId: number;
  sourceLocationId?: number;
  lineItems: any[];
  onFormSuccess: (response: any) => void;
}) {
  const [sourceLocation, setSourceLocation] = useState<number | null>(
    sourceLocationId || null
  );

  // Memoize the line items to prevent re-rendering
  const lines = useMemo(() => {
    return lineItems.map((item) => {
      return {
        id: item.pk,
        ...item
      };
    });
  }, [lineItems]);

  const fields: ApiFormFieldSet = useMemo(() => {
    return {
      // Non-submitted field to select the source location
      source_location: {
        exclude: true,
        required: false,
        value: sourceLocationId,
        field_type: 'related field',
        api_url: apiUrl(ApiEndpoints.stock_location_list),
        model: ModelType.stocklocation,
        label: t`Source Location`,
        description: t`Select the source location for the stock allocation`,
        onValueChange: (value: any) => {
          setSourceLocation(value);
        }
      },
      items: {
        field_type: 'table',
        value: lineItems,
        headers: [
          { title: t`Part`, style: { minWidth: '200px' } },
          { title: t`Allocated`, style: { minWidth: '200px' } },
          { title: t`Stock Item`, style: { width: '100%' } },
          { title: t`Quantity`, style: { minWidth: '200px' } },
          { title: '', style: { width: '50px' } }
        ],
        modelRenderer: (row: TableFieldRowProps) => {
          const record =
            lines.find((item) => item.pk == row.item.line_item) ?? {};

          return (
            <TransferOrderAllocateLineRow
              key={row.rowId}
              props={row}
              record={record}
              sourceLocation={sourceLocation}
            />
          );
        }
      }
    };
  }, [orderId, lineItems, sourceLocation]);

  return useCreateApiFormModal({
    title: t`Allocate Stock`,
    url: ApiEndpoints.transfer_order_allocate,
    pk: orderId,
    fields: fields,
    onFormSuccess: onFormSuccess,
    successMessage: t`Stock items allocated`,
    size: '80%',
    initialData: {
      items: lineItems.map((item) => {
        return {
          id: item.pk,
          line_item: item.pk,
          quantity: 0,
          stock_item: null
        };
      })
    }
  });
}

export function useTransferOrderAllocationFields({
  orderId
}: {
  orderId?: number;
}): ApiFormFieldSet {
  return useMemo(() => {
    return {
      item: {
        // Cannot change item, but display for reference
        disabled: true
      },
      quantity: {}
    };
  }, [orderId]);
}

export function useTransferOrderAllocateSerialsFields({
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
      serial_numbers: {}
    };
  }, [itemId, orderId]);
}
