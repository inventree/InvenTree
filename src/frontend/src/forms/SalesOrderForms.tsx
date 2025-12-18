import { t } from '@lingui/core/macro';
import { Alert, Table, Text } from '@mantine/core';
import {
  IconAddressBook,
  IconCalendar,
  IconCircleCheck,
  IconCircleX,
  IconCoins,
  IconUser,
  IconUsers
} from '@tabler/icons-react';
import { useEffect, useMemo, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import RemoveRowButton from '../components/buttons/RemoveRowButton';
import { StandaloneField } from '../components/forms/StandaloneField';

import { ProgressBar } from '@lib/components/ProgressBar';
import { apiUrl } from '@lib/functions/Api';
import { toNumber } from '@lib/functions/Conversion';
import type {
  ApiFormAdjustFilterType,
  ApiFormFieldSet,
  ApiFormFieldType
} from '@lib/types/Forms';
import type { TableFieldRowProps } from '../components/forms/fields/TableField';
import { useCreateApiFormModal, useEditApiFormModal } from '../hooks/UseForm';
import { useGlobalSettingsState } from '../states/SettingsStates';
import { useUserState } from '../states/UserState';
import { RenderPartColumn } from '../tables/ColumnRenderers';

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
  create,
  currency
}: {
  customerId?: number;
  orderId?: number;
  create?: boolean;
  currency?: string;
}): ApiFormFieldSet {
  const [salePrice, setSalePrice] = useState<string | undefined>(undefined);
  const [partCurrency, setPartCurrency] = useState<string>(currency ?? '');
  const [part, setPart] = useState<any>({});
  const [quantity, setQuantity] = useState<string>('1');

  // Update suggested sale price when part, quantity, or part currency changes
  useEffect(() => {
    // Only attempt to set sale price for new line items
    if (!create) return;

    const qty = toNumber(quantity, null);

    if (qty == null || qty <= 0) {
      setSalePrice(undefined);
      return;
    }

    if (!part || !part.price_breaks || part.price_breaks.length === 0) {
      setSalePrice(undefined);
      return;
    }

    const applicablePriceBreaks = part?.price_breaks
      ?.filter(
        (pb: any) => pb.price_currency == partCurrency && qty >= pb.quantity
      )
      .sort((a: any, b: any) => b.quantity - a.quantity);

    if (applicablePriceBreaks.length) {
      setSalePrice(applicablePriceBreaks[0].price);
    } else {
      setSalePrice(undefined);
    }
  }, [part, quantity, partCurrency, create]);

  return useMemo(() => {
    const fields: ApiFormFieldSet = {
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
          salable: true,
          price_breaks: true
        },
        onValueChange: (_: any, record?: any) => setPart(record)
      },
      reference: {},
      quantity: {
        onValueChange: (value) => {
          setQuantity(value);
        }
      },
      sale_price: {
        placeholder: salePrice,
        placeholderAutofill: true
      },
      sale_price_currency: {
        icon: <IconCoins />,
        value: partCurrency,
        onValueChange: setPartCurrency
      },
      project_code: {
        description: t`Select project code for this line item`
      },
      target_date: {},
      notes: {},
      link: {}
    };

    return fields;
  }, [salePrice, partCurrency, orderId, create]);
}

export function useCheckShipmentForm({
  shipmentId,
  onSuccess
}: {
  shipmentId: number;
  onSuccess: (response: any) => void;
}) {
  const user = useUserState();

  return useEditApiFormModal({
    url: ApiEndpoints.sales_order_shipment_list,
    pk: shipmentId,
    title: t`Check Shipment`,
    preFormContent: (
      <Alert color='green' icon={<IconCircleCheck />} title={t`Check Shipment`}>
        <Text>{t`Marking the shipment as checked indicates that you have verified that all items included in this shipment are correct`}</Text>
      </Alert>
    ),
    fetchInitialData: false,
    fields: {
      checked_by: {
        hidden: true,
        value: user.getUser()?.pk
      }
    },
    successMessage: t`Shipment marked as checked`,
    onFormSuccess: onSuccess
  });
}

export function useUncheckShipmentForm({
  shipmentId,
  onSuccess
}: {
  shipmentId: number;
  onSuccess: (response: any) => void;
}) {
  return useEditApiFormModal({
    url: ApiEndpoints.sales_order_shipment_list,
    pk: shipmentId,
    title: t`Uncheck Shipment`,
    preFormContent: (
      <Alert color='red' icon={<IconCircleX />} title={t`Uncheck Shipment`}>
        <Text>{t`Marking the shipment as unchecked indicates that the shipment requires further verification`}</Text>
      </Alert>
    ),
    fetchInitialData: false,
    fields: {
      checked_by: {
        hidden: true,
        value: null
      }
    },
    successMessage: t`Shipment marked as unchecked`,
    onFormSuccess: onSuccess
  });
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
  customerId,
  pending
}: {
  customerId?: number;
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
      shipment_address: {
        placeholder: t`Leave blank to use the order address`,
        filters: {
          company: customerId,
          ordering: '-primary'
        }
      },
      tracking_number: {},
      invoice_number: {},
      link: {}
    };
  }, [customerId, pending]);
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
