import { t } from '@lingui/macro';
import { Flex, FocusTrap, Modal, NumberInput, TextInput } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import {
  IconAddressBook,
  IconCalendar,
  IconCoins,
  IconCurrencyDollar,
  IconHash,
  IconLink,
  IconList,
  IconNotes,
  IconSitemap,
  IconUser,
  IconUsers
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';

import { api } from '../App';
import { ActionButton } from '../components/buttons/ActionButton';
import { StandaloneField } from '../components/forms/StandaloneField';
import {
  ApiFormAdjustFilterType,
  ApiFormFieldSet
} from '../components/forms/fields/ApiFormField';
import { Thumbnail } from '../components/images/Thumbnail';
import { ProgressBar } from '../components/items/ProgressBar';
import { StylishText } from '../components/items/StylishText';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { ModelType } from '../enums/ModelType';
import { InvenTreeIcon } from '../functions/icons';
import { useCreateApiFormModal } from '../hooks/UseForm';
import { apiUrl } from '../states/ApiState';

/*
 * Construct a set of fields for creating / editing a PurchaseOrderLineItem instance
 */
export function usePurchaseOrderLineItemFields({
  create
}: {
  create?: boolean;
}) {
  const [purchasePrice, setPurchasePrice] = useState<string>('');
  const [autoPricing, setAutoPricing] = useState(true);

  useEffect(() => {
    if (autoPricing) {
      setPurchasePrice('');
    }
  }, [autoPricing]);

  useEffect(() => {
    setAutoPricing(purchasePrice === '');
  }, [purchasePrice]);

  const fields = useMemo(() => {
    const fields: ApiFormFieldSet = {
      order: {
        filters: {
          supplier_detail: true
        },
        hidden: true
      },
      part: {
        filters: {
          part_detail: true,
          supplier_detail: true
        },
        adjustFilters: (value: ApiFormAdjustFilterType) => {
          // TODO: Adjust part based on the supplier associated with the supplier
          return value.filters;
        }
      },
      quantity: {},
      reference: {},
      purchase_price: {
        icon: <IconCurrencyDollar />,
        value: purchasePrice,
        onValueChange: setPurchasePrice
      },
      purchase_price_currency: {
        icon: <IconCoins />
      },
      auto_pricing: {
        value: autoPricing,
        onValueChange: setAutoPricing
      },
      target_date: {
        icon: <IconCalendar />
      },
      destination: {
        icon: <IconSitemap />
      },
      notes: {
        icon: <IconNotes />
      },
      link: {
        icon: <IconLink />
      }
    };

    if (create) {
      fields['merge_items'] = {};
    }

    return fields;
  }, [create, autoPricing, purchasePrice]);

  return fields;
}

/**
 * Construct a set of fields for creating / editing a PurchaseOrder instance
 */
export function purchaseOrderFields(): ApiFormFieldSet {
  return {
    reference: {
      icon: <IconHash />
    },
    description: {},
    supplier: {
      filters: {
        is_supplier: true
      }
    },
    supplier_reference: {},
    project_code: {
      icon: <IconList />
    },
    order_currency: {
      icon: <IconCoins />
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
          company: value.data.supplier
        };
      }
    },
    address: {
      icon: <IconAddressBook />,
      adjustFilters: (value: ApiFormAdjustFilterType) => {
        return {
          ...value.filters,
          company: value.data.supplier
        };
      }
    },
    responsible: {
      icon: <IconUsers />
    }
  };
}

/**
 * Render a table row for a single TableField entry
 */
function LineItemFormRow({
  input,
  record,
  statuses
}: {
  input: any;
  record: any;
  statuses: any;
}) {
  // Barcode Modal state
  const [opened, { open, close }] = useDisclosure(false);

  // Location value
  const [location, setLocation] = useState(input.item.location);
  const [locationOpen, locationHandlers] = useDisclosure(
    input.item.location ? true : false,
    {
      onClose: () => input.changeFn(input.idx, 'location', null),
      onOpen: () => input.changeFn(input.idx, 'location', location)
    }
  );

  // Change form value when state is altered
  useEffect(() => {
    input.changeFn(input.idx, 'location', location);
  }, [location]);

  // State for serializing
  const [batchCode, setBatchCode] = useState<string>('');
  const [serials, setSerials] = useState<string>('');
  const [batchOpen, batchHandlers] = useDisclosure(false, {
    onClose: () => {
      input.changeFn(input.idx, 'batch_code', '');
      input.changeFn(input.idx, 'serial_numbers', '');
    }
  });

  // Change form value when state is altered
  useEffect(() => {
    input.changeFn(input.idx, 'batch_code', batchCode);
  }, [batchCode]);

  // Change form value when state is altered
  useEffect(() => {
    input.changeFn(input.idx, 'serial_numbers', serials);
  }, [serials]);

  // Status value
  const [statusOpen, statusHandlers] = useDisclosure(false, {
    onClose: () => input.changeFn(input.idx, 'status', 10)
  });

  // Barcode value
  const [barcodeInput, setBarcodeInput] = useState<any>('');
  const [barcode, setBarcode] = useState(null);

  // Change form value when state is altered
  useEffect(() => {
    input.changeFn(input.idx, 'barcode', barcode);
  }, [barcode]);

  // Update location field description on state change
  useEffect(() => {
    if (!opened) {
      return;
    }

    const timeoutId = setTimeout(() => {
      setBarcode(barcodeInput.length ? barcodeInput : null);
      close();
      setBarcodeInput('');
    }, 500);
    return () => clearTimeout(timeoutId);
  }, [barcodeInput]);

  const locationDescription = useMemo(() => {
    let text = t`Choose Location`;

    if (location === null) {
      return text;
    }

    if (location === record.part_detail.default_location) {
      return t`Default location selected`;
    } else if (location === record.destination) {
      return t`Item Destination selected`;
    } else if (
      !record.destination &&
      location === record.destination_detail.pk
    ) {
      return t`Received stock location selected`;
    }

    return text;
  }, [location]);

  return (
    <>
      <Modal
        opened={opened}
        onClose={close}
        title={<StylishText children={t`Scan Barcode`} />}
      >
        <FocusTrap>
          <TextInput
            label="Barcode data"
            data-autofocus
            value={barcodeInput}
            onChange={(e) => setBarcodeInput(e.target.value)}
          />
        </FocusTrap>
      </Modal>
      <tr>
        <td>
          <Flex gap="sm" align="center">
            <Thumbnail
              size={40}
              src={record.part_detail.thumbnail}
              align="center"
            />
            <div>{record.part_detail.name}</div>
          </Flex>
        </td>
        <td>{record.supplier_part_detail.SKU}</td>
        <td>
          <ProgressBar
            value={record.received}
            maximum={record.quantity}
            progressLabel
          />
        </td>
        <td>
          <NumberInput
            value={input.item.quantity}
            style={{ maxWidth: '100px' }}
            max={input.item.quantity}
            min={0}
            onChange={(value) => input.changeFn(input.idx, 'quantity', value)}
          />
        </td>
        <td>
          <Flex gap="1px">
            <ActionButton
              onClick={() => locationHandlers.toggle()}
              icon={<InvenTreeIcon icon="location" />}
              tooltip={t`Set Location`}
              tooltipAlignment="top"
              variant={locationOpen ? 'filled' : 'outline'}
            />
            <ActionButton
              onClick={() => batchHandlers.toggle()}
              icon={<InvenTreeIcon icon="batch_code" />}
              tooltip={t`Assign Batch Code${
                record.trackable && ' and Serial Numbers'
              }`}
              tooltipAlignment="top"
              variant={batchOpen ? 'filled' : 'outline'}
            />
            <ActionButton
              onClick={() => statusHandlers.toggle()}
              icon={<InvenTreeIcon icon="status" />}
              tooltip={t`Change Status`}
              tooltipAlignment="top"
              variant={statusOpen ? 'filled' : 'outline'}
            />
            {barcode ? (
              <ActionButton
                icon={<InvenTreeIcon icon="unlink" />}
                tooltip={t`Unlink Barcode`}
                tooltipAlignment="top"
                variant="filled"
                color="red"
                onClick={() => setBarcode(null)}
              />
            ) : (
              <ActionButton
                icon={<InvenTreeIcon icon="barcode" />}
                tooltip={t`Scan Barcode`}
                tooltipAlignment="top"
                variant="outline"
                onClick={() => open()}
              />
            )}
            <ActionButton
              onClick={() => input.removeFn(input.idx)}
              icon={<InvenTreeIcon icon="square_x" />}
              tooltip={t`Remove item from list`}
              tooltipAlignment="top"
              color="red"
            />
          </Flex>
        </td>
      </tr>
      {locationOpen && (
        <tr>
          <td colSpan={4}>
            <Flex align="end" gap={5}>
              <div style={{ flexGrow: '1' }}>
                <StandaloneField
                  fieldDefinition={{
                    field_type: 'related field',
                    model: ModelType.stocklocation,
                    api_url: apiUrl(ApiEndpoints.stock_location_list),
                    filters: {
                      structural: false
                    },
                    onValueChange: (value) => {
                      setLocation(value);
                    },
                    description: locationDescription,
                    value: location,
                    label: t`Location`,
                    icon: <InvenTreeIcon icon="location" />
                  }}
                  defaultValue={
                    record.destination ??
                    (record.destination_detail
                      ? record.destination_detail.pk
                      : null)
                  }
                />
              </div>
              <Flex style={{ marginBottom: '7px' }}>
                {(record.part_detail.default_location ||
                  record.part_detail.category_default_location) && (
                  <ActionButton
                    icon={<InvenTreeIcon icon="default_location" />}
                    tooltip={t`Store at default location`}
                    onClick={() =>
                      setLocation(
                        record.part_detail.default_location ??
                          record.part_detail.category_default_location
                      )
                    }
                    tooltipAlignment="top"
                  />
                )}
                {record.destination && (
                  <ActionButton
                    icon={<InvenTreeIcon icon="destination" />}
                    tooltip={t`Store at line item destination `}
                    onClick={() => setLocation(record.destination)}
                    tooltipAlignment="top"
                  />
                )}
                {!record.destination &&
                  !record.part_detail.default_location &&
                  record.destination_detail && (
                    <ActionButton
                      icon={<InvenTreeIcon icon="repeat_destination" />}
                      tooltip={t`Store with already received stock`}
                      onClick={() => setLocation(record.destination_detail.pk)}
                      tooltipAlignment="top"
                    />
                  )}
              </Flex>
            </Flex>
          </td>
          <td>
            <div
              style={{
                height: '100%',
                display: 'grid',
                gridTemplateColumns: 'repeat(6, 1fr)',
                gridTemplateRows: 'auto',
                alignItems: 'end'
              }}
            >
              <InvenTreeIcon icon="downleft" />
            </div>
          </td>
        </tr>
      )}
      {batchOpen && (
        <>
          <tr>
            <td colSpan={4}>
              <Flex align="end" gap={5}>
                <div style={{ flexGrow: '1' }}>
                  <StandaloneField
                    fieldDefinition={{
                      field_type: 'string',
                      onValueChange: (value) => setBatchCode(value),
                      label: 'Batch Code',
                      value: batchCode
                    }}
                  />
                </div>
              </Flex>
            </td>
            <td>
              <div
                style={{
                  height: '100%',
                  display: 'grid',
                  gridTemplateColumns: 'repeat(6, 1fr)',
                  gridTemplateRows: 'auto',
                  alignItems: 'end'
                }}
              >
                <span></span>
                <InvenTreeIcon icon="downleft" />
              </div>
            </td>
          </tr>
          {record.trackable && (
            <tr>
              <td colSpan={4}>
                <Flex align="end" gap={5}>
                  <div style={{ flexGrow: '1' }}>
                    <StandaloneField
                      fieldDefinition={{
                        field_type: 'string',
                        onValueChange: (value) => setSerials(value),
                        label: 'Serial numbers',
                        value: serials
                      }}
                    />
                  </div>
                </Flex>
              </td>
              <td>
                <div
                  style={{
                    height: '100%',
                    display: 'grid',
                    gridTemplateColumns: 'repeat(6, 1fr)',
                    gridTemplateRows: 'auto',
                    alignItems: 'end'
                  }}
                >
                  <span></span>
                  <InvenTreeIcon icon="downleft" />
                </div>
              </td>
            </tr>
          )}
        </>
      )}
      {statusOpen && (
        <tr>
          <td colSpan={4}>
            <StandaloneField
              fieldDefinition={{
                field_type: 'choice',
                api_url: apiUrl(ApiEndpoints.stock_status),
                choices: statuses,
                label: 'Status',
                onValueChange: (value) =>
                  input.changeFn(input.idx, 'status', value)
              }}
              defaultValue={10}
            />
          </td>
          <td>
            <div
              style={{
                height: '100%',
                display: 'grid',
                gridTemplateColumns: 'repeat(6, 1fr)',
                gridTemplateRows: 'auto',
                alignItems: 'end'
              }}
            >
              <span></span>
              <span></span>
              <InvenTreeIcon icon="downleft" />
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

type LineFormHandlers = {
  onOpen?: () => void;
  onClose?: () => void;
};

type LineItemsForm = {
  items: any[];
  orderPk: number;
  formProps?: LineFormHandlers;
};

export function useReceiveLineItems(props: LineItemsForm) {
  const { data } = useQuery({
    queryKey: ['stock', 'status'],
    queryFn: async () => {
      return api.get(apiUrl(ApiEndpoints.stock_status)).then((response) => {
        if (response.status === 200) {
          const entries = Object.values(response.data.values);
          const mapped = entries.map((item: any) => {
            return {
              value: item.key,
              display_name: item.label
            };
          });
          return mapped;
        }
      });
    }
  });

  const records = Object.fromEntries(
    props.items.map((item) => [item.pk, item])
  );

  const filteredItems = props.items.filter(
    (elem) => elem.quantity !== elem.received
  );

  const fields: ApiFormFieldSet = {
    id: {
      value: props.orderPk,
      hidden: true
    },
    items: {
      field_type: 'table',
      value: filteredItems.map((elem, idx) => {
        return {
          line_item: elem.pk,
          location: elem.destination ?? elem.destination_detail?.pk ?? null,
          quantity: elem.quantity - elem.received,
          batch_code: '',
          serial_numbers: '',
          status: 10,
          barcode: null
        };
      }),
      modelRenderer: (instance) => {
        const record = records[instance.item.line_item];

        return (
          <LineItemFormRow
            input={instance}
            record={record}
            statuses={data}
            key={record.pk}
          />
        );
      },
      headers: ['Part', 'SKU', 'Received', 'Quantity to receive', 'Actions']
    },
    location: {
      filters: {
        structural: false
      }
    }
  };

  const url = apiUrl(ApiEndpoints.purchase_order_receive, null, {
    id: props.orderPk
  });

  return useCreateApiFormModal({
    ...props.formProps,
    url: url,
    title: t`Receive line items`,
    fields: fields,
    initialData: {
      location: null
    }
  });
}
