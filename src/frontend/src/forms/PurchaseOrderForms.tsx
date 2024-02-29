import { t } from '@lingui/macro';
import { Flex, NumberInput } from '@mantine/core';
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
import Select from 'react-select';

import { api } from '../App';
import {
  ApiFormAdjustFilterType,
  ApiFormFieldSet
} from '../components/forms/fields/ApiFormField';
import { Thumbnail } from '../components/images/Thumbnail';
import { ProgressBar } from '../components/items/ProgressBar';
import { ApiEndpoints } from '../enums/ApiEndpoints';
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
  console.log('status', statuses);
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
            value={item.quantity}
            style={{ maxWidth: '100px' }}
            max={item.quantity}
            min={0}
          />
        </td>
        <td>
          <Select options={statuses} value={10} />
        </td>
        <td>sss</td>
      </tr>
      <tr style={{ display: 'none' }}>
        <th>Location:</th>
        <td></td>
      </tr>
      <tr style={{ display: 'none' }}>
        <th>Loc:</th>
        <td>aaa</td>
      </tr>
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
  console.log(items);

  const { data } = useQuery({
    queryKey: ['stock', 'status'],
    queryFn: async () => {
      return api.get(apiUrl(ApiEndpoints.stock_status)).then((response) => {
        if (response.status === 200) {
          const entries = Object.entries(response.data.values);
          return entries.map((item: any) => {
            console.log(item[1]);
            return {
              value: item[1].key,
              label: item[1].label
            };
          });
        }
      });
    }
  });

  const records = Object.fromEntries(items.map((item) => [item.pk, item]));

  const fields: ApiFormFieldSet = {
    id: {
      value: orderPk,
      hidden: true
    },
    items: {
      field_type: 'table',
      value: items.map((elem, idx) => {
        return {
          line_item: elem.pk,
          location:
            elem.destination ?? elem.part_detail.default_location ?? null,
          quantity: elem.quantity - elem.received,
          batch_code: null,
          serial_numbers: null,
          status: null,
          barcode: null
        };
      }),
      modelRenderer: (instance) => {
        console.log(instance);
        return (
          <LineItemFormRow
            item={instance.item}
            record={records[instance.item.line_item]}
            statuses={data}
          />
        );
      },
      headers: [
        'Part',
        'SKU',
        'Received',
        'Quantity to receive',
        'Status',
        'Actions'
      ]
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

  console.log(fields);
}
