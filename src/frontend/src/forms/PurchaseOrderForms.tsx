import { t } from '@lingui/macro';
import { Flex, NumberInput, Text } from '@mantine/core';
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
import { url } from 'inspector';
import { useEffect, useMemo, useState } from 'react';
import Select from 'react-select';

import { api } from '../App';
import { ActionButton } from '../components/buttons/ActionButton';
import { StandaloneField } from '../components/forms/StandaloneField';
import {
  ApiFormAdjustFilterType,
  ApiFormFieldSet
} from '../components/forms/fields/ApiFormField';
import { Thumbnail } from '../components/images/Thumbnail';
import { ProgressBar } from '../components/items/ProgressBar';
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

function LineItemFormRow({
  item,
  record,
  statuses
}: {
  item: any;
  record: any;
  statuses: any;
}) {
  const [location, setLocation] = useState(item.item.location);
  const [locationOpen, locationHandlers] = useDisclosure(
    item.item.location ? true : false,
    {
      onClose: () => item.changeFn(item.idx, 'location', null),
      onOpen: () => item.changeFn(item.idx, 'location', location)
    }
  );

  const [batchOpen, batchHandlers] = useDisclosure(false, {
    onClose: () => item.changeFn(item.idx, 'batch_code', null)
  });

  const [statusOpen, statusHandlers] = useDisclosure(false, {
    onClose: () => item.changeFn(item.idx, 'status', 10)
  });

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
            value={item.item.quantity}
            style={{ maxWidth: '100px' }}
            max={item.item.quantity}
            min={0}
          />
        </td>
        <td>
          <Flex>
            <ActionButton
              onClick={() => locationHandlers.toggle()}
              icon={<InvenTreeIcon icon="location" />}
              tooltip={t`Set Location`}
              tooltipAlignment="top"
            />
            <ActionButton
              onClick={() => batchHandlers.toggle()}
              icon={<InvenTreeIcon icon="batch_code" />}
              tooltip={t`Assign Batch Code`}
              tooltipAlignment="top"
            />
            <ActionButton
              onClick={() => statusHandlers.toggle()}
              icon={<InvenTreeIcon icon="status" />}
              tooltip={t`Change Status`}
              tooltipAlignment="top"
            />
            <ActionButton
              icon={<InvenTreeIcon icon="barcode" />}
              tooltip={t`Scan Barcode`}
              tooltipAlignment="top"
            />
            <ActionButton
              onClick={() => item.removeFn(item.idx)}
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
                      item.changeFn(item.idx, 'location', value);
                    },
                    description: locationDescription,
                    value: location,
                    label: t`Location`
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
        <tr>
          <td colSpan={4}>
            <Flex align="end" gap={5}>
              <div style={{ flexGrow: '1' }}>
                <StandaloneField
                  fieldDefinition={{
                    field_type: 'string',
                    onValueChange: (value) =>
                      item.changeFn(item.idx, 'batch_code', value),
                    label: 'Batch Code'
                  }}
                />
              </div>
            </Flex>
          </td>
          <td
            style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)' }}
          >
            <span></span>
            <InvenTreeIcon icon="downleft" />
          </td>
        </tr>
      )}
      {statusOpen && (
        <tr>
          <td colSpan={4}>
            <StandaloneField
              fieldDefinition={{
                field_type: 'choice',
                api_url: apiUrl(ApiEndpoints.stock_status),
                choices: statuses,
                label: 'Status'
              }}
              defaultValue={10}
            />
          </td>
          <td
            style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)' }}
          >
            <span></span>
            <span></span>
            <InvenTreeIcon icon="downleft" />
          </td>
        </tr>
      )}
    </>
  );
}

export function useReceiveLineItems({
  items,
  orderPk
}: {
  items: any[];
  orderPk: number;
}) {
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

  const records = Object.fromEntries(items.map((item) => [item.pk, item]));

  const filteredItems = items.filter((elem) => elem.quantity !== elem.received);

  const fields: ApiFormFieldSet = {
    id: {
      value: orderPk,
      hidden: true
    },
    items: {
      field_type: 'table',
      value: filteredItems.map((elem, idx) => {
        return {
          line_item: elem.pk,
          location: elem.destination ?? elem.destination_detail?.pk ?? null,
          quantity: elem.quantity - elem.received,
          batch_code: null,
          serial_numbers: null,
          status: 10,
          barcode: null
        };
      }),
      modelRenderer: (instance) => {
        const record = records[instance.item.line_item];

        return (
          <LineItemFormRow
            item={instance}
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
    id: orderPk
  });

  return useCreateApiFormModal({
    url: url,
    title: t`Receive line items`,
    fields: fields
  });
}
