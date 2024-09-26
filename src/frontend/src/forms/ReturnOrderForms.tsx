import { t } from '@lingui/macro';
import { Flex, Table } from '@mantine/core';
import { IconAddressBook, IconUser, IconUsers } from '@tabler/icons-react';
import { useMemo } from 'react';

import RemoveRowButton from '../components/buttons/RemoveRowButton';
import {
  ApiFormAdjustFilterType,
  ApiFormFieldSet
} from '../components/forms/fields/ApiFormField';
import { TableFieldRowProps } from '../components/forms/fields/TableField';
import { Thumbnail } from '../components/images/Thumbnail';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { useCreateApiFormModal } from '../hooks/UseForm';
import { apiUrl } from '../states/ApiState';

export function useReturnOrderFields({
  duplicateOrderId
}: {
  duplicateOrderId?: number;
}): ApiFormFieldSet {
  return useMemo(() => {
    let fields: ApiFormFieldSet = {
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
      target_date: {},
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
            // Cannot duplicate lines from a return order!
            value: false,
            hidden: true
          },
          copy_extra_lines: {}
        }
      };
    }

    return fields;
  }, [duplicateOrderId]);
}

export function useReturnOrderLineItemFields({
  orderId,
  customerId,
  create
}: {
  orderId: number;
  customerId: number;
  create?: boolean;
}) {
  return useMemo(() => {
    return {
      order: {
        disabled: true,
        filters: {
          customer_detail: true
        }
      },
      item: {
        filters: {
          customer: customerId,
          part_detail: true,
          serialized: true
        }
      },
      reference: {},
      outcome: {
        hidden: create == true
      },
      price: {},
      price_currency: {},
      target_date: {},
      notes: {},
      link: {},
      responsible: {
        filters: {
          is_active: true
        },
        icon: <IconUsers />
      }
    };
  }, [create, orderId, customerId]);
}

type ReturnOrderLineItemsProps = {
  items: any[];
  orderId: number;
  onFormSuccess: (data: any) => void;
};

function ReturnOrderLineItemFormRow({
  props,
  record
}: Readonly<{
  props: TableFieldRowProps;
  record: any;
}>) {
  return (
    <>
      <Table.Tr>
        <Table.Td>
          <Flex gap="sm" align="center">
            <Thumbnail
              size={40}
              src={record.part_detail.thumbnail}
              align="center"
            />
            <div>{record.part_detail.name}</div>
          </Flex>
        </Table.Td>
        <Table.Td>{record.item_detail.serial}</Table.Td>
        <Table.Td>
          <RemoveRowButton onClick={() => props.removeFn(props.idx)} />
        </Table.Td>
      </Table.Tr>
    </>
  );
}

export function useReceiveReturnOrderLineItems(
  props: ReturnOrderLineItemsProps
) {
  const fields: ApiFormFieldSet = {
    id: {
      value: props.orderId,
      hidden: true
    },
    items: {
      field_type: 'table',
      value: props.items.map((item: any) => {
        return {
          item: item.pk
        };
      }),
      modelRenderer: (row: TableFieldRowProps) => {
        const record = props.items.find((item) => item.pk == row?.item?.item);

        return (
          <ReturnOrderLineItemFormRow
            props={row}
            record={record}
            key={record.pk}
          />
        );
      },
      headers: [t`Part`, t`Serial Number`]
    },
    location: {
      filters: {
        structural: false
      }
    }
  };

  return useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.return_order_receive, props.orderId),
    title: t`Receive Items`,
    fields: fields,
    initialData: {
      location: null
    },
    size: '80%',
    onFormSuccess: props.onFormSuccess,
    successMessage: t`Item received into stock`
  });
}
