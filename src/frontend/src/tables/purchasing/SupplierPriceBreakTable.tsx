import { t } from '@lingui/macro';
import { Anchor, Group, Text } from '@mantine/core';
import { useCallback, useMemo, useState } from 'react';

import { Thumbnail } from '@lib/components';
import { AddItemButton } from '@lib/components/buttons/AddItemButton';
import { ApiEndpoints } from '@lib/core';
import { ModelType } from '@lib/core';
import { UserRoles } from '@lib/core';
import type { ApiFormFieldSet } from '@lib/forms';
import { apiUrl, getBaseUrl } from '@lib/functions';
import { getDetailUrl } from '@lib/functions';
import { formatCurrency } from '@lib/functions';
import { useTable } from '@lib/hooks';
import { useUserState } from '@lib/states';
import type { RowAction, TableColumn } from '@lib/tables';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowDeleteAction, RowEditAction } from '../RowActions';

export function calculateSupplierPartUnitPrice(record: any) {
  const pack_quantity = record?.part_detail?.pack_quantity_native ?? 1;
  const unit_price = Number.parseFloat(record.price) / pack_quantity;

  return unit_price;
}

export function SupplierPriceBreakColumns(): TableColumn[] {
  const base_url = getBaseUrl();

  return [
    {
      accessor: 'supplier',
      title: t`Supplier`,
      sortable: true,
      switchable: true,
      render: (record: any) => {
        return (
          <Group gap='xs' wrap='nowrap'>
            <Thumbnail
              src={
                record?.supplier_detail?.thumbnail ??
                record?.supplier_detail?.image
              }
              alt={record?.supplier_detail?.name}
              size={24}
            />
            <Text>{record.supplier_detail?.name}</Text>
          </Group>
        );
      }
    },
    {
      accessor: 'part_detail.SKU',
      title: t`SKU`,
      ordering: 'SKU',
      sortable: true,
      switchable: false,
      render: (record: any) => {
        return (
          <Anchor
            href={getDetailUrl(
              ModelType.supplierpart,
              record.part_detail.pk,
              base_url,
              true
            )}
          >
            {record.part_detail.SKU}
          </Anchor>
        );
      }
    },
    {
      accessor: 'quantity',
      title: t`Quantity`,
      sortable: true,
      switchable: false
    },
    {
      accessor: 'price',
      title: t`Supplier Price`,
      render: (record: any) =>
        formatCurrency(record.price, { currency: record.price_currency }),
      sortable: true,
      switchable: false
    },
    {
      accessor: 'unit_price',
      ordering: 'price',
      title: t`Unit Price`,
      sortable: true,
      switchable: true,
      render: (record: any) => {
        const units = record.part_detail?.pack_quantity;

        const price = formatCurrency(calculateSupplierPartUnitPrice(record), {
          currency: record.price_currency
        });

        return (
          <Group justify='space-between' gap='xs' grow>
            <Text>{price}</Text>
            {units && <Text size='xs'>[{units}]</Text>}
          </Group>
        );
      }
    }
  ];
}

export default function SupplierPriceBreakTable({
  supplierPart
}: Readonly<{
  supplierPart: any;
}>) {
  const table = useTable('supplierpricebreaks');

  const user = useUserState();

  const columns: TableColumn[] = useMemo(() => {
    return SupplierPriceBreakColumns();
  }, []);

  const supplierPriceBreakFields: ApiFormFieldSet = useMemo(() => {
    return {
      part: {
        hidden: false,
        disabled: true
      },
      quantity: {},
      price: {},
      price_currency: {}
    };
  }, []);

  const [selectedPriceBreak, setSelectedPriceBreak] = useState<number>(0);

  const newPriceBreak = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.supplier_part_pricing_list),
    title: t`Add Price Break`,
    fields: supplierPriceBreakFields,
    initialData: {
      part: supplierPart.pk,
      price_currency: supplierPart.supplier_detail.currency
    },
    table: table
  });

  const editPriceBreak = useEditApiFormModal({
    url: apiUrl(ApiEndpoints.supplier_part_pricing_list),
    pk: selectedPriceBreak,
    title: t`Edit Price Break`,
    fields: supplierPriceBreakFields,
    table: table
  });

  const deletePriceBreak = useDeleteApiFormModal({
    url: apiUrl(ApiEndpoints.supplier_part_pricing_list),
    pk: selectedPriceBreak,
    title: t`Delete Price Break`,
    table: table
  });

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-price-break'
        tooltip={t`Add Price Break`}
        onClick={() => {
          newPriceBreak.open();
        }}
        hidden={!user.hasAddRole(UserRoles.part)}
      />
    ];
  }, [user]);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.purchase_order),
          onClick: () => {
            setSelectedPriceBreak(record.pk);
            editPriceBreak.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.purchase_order),
          onClick: () => {
            setSelectedPriceBreak(record.pk);
            deletePriceBreak.open();
          }
        })
      ];
    },
    [user]
  );

  return (
    <>
      {newPriceBreak.modal}
      {editPriceBreak.modal}
      {deletePriceBreak.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.supplier_part_pricing_list)}
        columns={columns}
        tableState={table}
        props={{
          params: {
            part: supplierPart.pk,
            part_detail: true,
            supplier_detail: true
          },
          tableActions: tableActions,
          rowActions: rowActions
        }}
      />
    </>
  );
}
