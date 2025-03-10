import { t } from '@lingui/macro';
import { Table } from '@mantine/core';
import {
  IconAddressBook,
  IconCalendar,
  IconUser,
  IconUsers
} from '@tabler/icons-react';
import { useEffect, useMemo, useState } from 'react';

import RemoveRowButton from '../components/buttons/RemoveRowButton';
import { StandaloneField } from '../components/forms/StandaloneField';
import type {
  ApiFormAdjustFilterType,
  ApiFormFieldSet,
  ApiFormFieldType
} from '../components/forms/fields/ApiFormField';
import type { TableFieldRowProps } from '../components/forms/fields/TableField';
import { ProgressBar } from '../components/items/ProgressBar';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { ModelType } from '../enums/ModelType';
import { useCreateApiFormModal } from '../hooks/UseForm';
import { apiUrl } from '../states/ApiState';
import { useGlobalSettingsState } from '../states/SettingsState';
import { PartColumn } from '../tables/ColumnRenderers';

export function useSalesOrderFields({
  duplicateOrderId
}: {
  duplicateOrderId?: number;
}): ApiFormFieldSet {
  const globalSettings = useGlobalSettingsState();

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
      customer_reference: {},
      project_code: {},
      order_currency: {},
      start_date: {
        icon: <IconCalendar />
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

    if (!globalSettings.isSet('PROJECT_CODES_ENABLED', true)) {
      delete fields.project_code;
    }

    return fields;
  }, [duplicateOrderId, globalSettings]);
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

function SalesOrderAllocateLineRow({
  props,
  record,
  sourceLocation
}: Readonly<{
  props: TableFieldRowProps;
  record: any;
  sourceLocation?: number | null;
}>) {
  // Statically defined field for selecting the stock item
  const stockItemField: ApiFormFieldType = useMemo(() => {
    return {
      field_type: 'related field',
      api_url: apiUrl(ApiEndpoints.stock_item_list),
      model: ModelType.stockitem,
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
        props.changeFn(props.idx, 'stock_item', value);

        // Update the allocated quantity based on the selected stock item
        if (instance) {
          const available = instance.quantity - instance.allocated;
          const required = record.quantity - record.allocated;

          let quantity = props.item?.quantity ?? 0;

          quantity = Math.max(quantity, required);
          quantity = Math.min(quantity, available);

          if (quantity != props.item.quantity) {
            props.changeFn(props.idx, 'quantity', quantity);
          }
        }
      }
    };
  }, [sourceLocation, record, props]);

  // Statically defined field for selecting the allocation quantity
  const quantityField: ApiFormFieldType = useMemo(() => {
    return {
      field_type: 'number',
      name: 'quantity',
      required: true,
      value: props.item.quantity,
      onValueChange: (value: any) => {
        props.changeFn(props.idx, 'quantity', value);
      }
    };
  }, [props]);

  return (
    <Table.Tr key={`table-row-${props.idx}-${record.pk}`}>
      <Table.Td>
        <PartColumn part={record.part_detail} />
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
        <StandaloneField
          fieldName='quantity'
          fieldDefinition={quantityField}
          error={props.rowErrors?.quantity?.message}
        />
      </Table.Td>
      <Table.Td>
        <RemoveRowButton onClick={() => props.removeFn(props.idx)} />
      </Table.Td>
    </Table.Tr>
  );
}

export function useAllocateToSalesOrderForm({
  orderId,
  shipmentId,
  lineItems,
  onFormSuccess
}: {
  orderId: number;
  shipmentId?: number;
  lineItems: any[];
  onFormSuccess: (response: any) => void;
}) {
  const [sourceLocation, setSourceLocation] = useState<number | null>(null);

  // Reset source location to known state
  useEffect(() => {
    setSourceLocation(null);
  }, [orderId, shipmentId, lineItems]);

  const fields: ApiFormFieldSet = useMemo(() => {
    return {
      // Non-submitted field to select the source location
      source_location: {
        exclude: true,
        required: false,
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
        value: [],
        headers: [
          { title: t`Part`, style: { minWidth: '200px' } },
          { title: t`Allocated`, style: { minWidth: '200px' } },
          { title: t`Stock Item`, style: { width: '100%' } },
          { title: t`Quantity`, style: { minWidth: '200px' } },
          { title: '', style: { width: '50px' } }
        ],
        modelRenderer: (row: TableFieldRowProps) => {
          const record =
            lineItems.find((item) => item.pk == row.item.line_item) ?? {};

          return (
            <SalesOrderAllocateLineRow
              key={`table-row-${row.idx}-${record.pk}`}
              props={row}
              record={record}
              sourceLocation={sourceLocation}
            />
          );
        }
      },
      shipment: {
        filters: {
          shipped: false,
          order_detail: true,
          order: orderId
        }
      }
    };
  }, [orderId, shipmentId, lineItems, sourceLocation]);

  return useCreateApiFormModal({
    title: t`Allocate Stock`,
    url: ApiEndpoints.sales_order_allocate,
    pk: orderId,
    fields: fields,
    onFormSuccess: onFormSuccess,
    successMessage: t`Stock items allocated`,
    size: '80%',
    initialData: {
      items: lineItems.map((item) => {
        return {
          line_item: item.pk,
          quantity: 0,
          stock_item: null
        };
      })
    }
  });
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
  orderId,
  shipment
}: {
  orderId?: number;
  shipment: any;
}): ApiFormFieldSet {
  return useMemo(() => {
    return {
      item: {
        // Cannot change item, but display for reference
        disabled: true
      },
      quantity: {},
      shipment: {
        // Cannot change shipment once it has been shipped
        disabled: !!shipment?.shipment_date,
        // Order ID is required for this field to be accessed
        hidden: !orderId,
        filters: {
          order: orderId,
          shipped: false
        }
      }
    };
  }, [orderId, shipment]);
}
