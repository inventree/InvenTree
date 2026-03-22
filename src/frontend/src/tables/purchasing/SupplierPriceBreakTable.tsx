import { t } from '@lingui/core/macro';
import { Anchor, Group, Text } from '@mantine/core';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import {
  type RowAction,
  RowDeleteAction,
  RowEditAction
} from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { getDetailUrl } from '@lib/functions/Navigation';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import type { TableColumn } from '@lib/types/Tables';
import { formatCurrency } from '../../defaults/formatters';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import { CompanyColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

export function calculateSupplierPartUnitPrice(record: any) {
  const pack_quantity = record?.part_detail?.pack_quantity_native ?? 1;
  const unit_price = Number.parseFloat(record.price) / pack_quantity;

  return unit_price;
}

export function SupplierPriceBreakColumns(): TableColumn[] {
  return [
    {
      accessor: 'supplier',
      title: t`Supplier`,
      sortable: true,
      switchable: true,
      render: (record: any) => (
        <CompanyColumn company={record.supplier_detail} />
      )
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
          rowActions: rowActions,
          enableDownload: true
        }}
      />
    </>
  );
}
