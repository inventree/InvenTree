import { t } from '@lingui/macro';
import { Flex, Table } from '@mantine/core';
import { IconUsers } from '@tabler/icons-react';
import { useMemo } from 'react';

import RemoveRowButton from '../components/buttons/RemoveRowButton';
import { ApiFormFieldSet } from '../components/forms/fields/ApiFormField';
import { TableFieldRowProps } from '../components/forms/fields/TableField';
import { Thumbnail } from '../components/images/Thumbnail';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { useCreateApiFormModal } from '../hooks/UseForm';
import { apiUrl } from '../states/ApiState';

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
