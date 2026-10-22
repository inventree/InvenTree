import { t } from '@lingui/core/macro';
import { Alert, Anchor, Group, Stack, Text } from '@mantine/core';
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
import { formatDecimal } from '@lib/functions/Formatting';
import { getDetailUrl } from '@lib/functions/Navigation';
import useTable from '@lib/hooks/UseTable';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import type { TableColumn } from '@lib/types/Tables';
import { CompanyColumn } from '../../components/tables/ColumnRenderers';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import { formatCurrency } from '../../defaults/formatters';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useUserState } from '../../states/UserState';

export function calculateSupplierPartUnitPrice(record: any) {
  const pack_quantity = record?.part_detail?.pack_quantity_native ?? 1;
  const unit_price = Number.parseFloat(record.price) / pack_quantity;

  return unit_price;
}

/**
 * Construct table columns for supplier price breaks
 * @param units - The units of measure for the base part (the "unit" in "unit price")
 */
export function SupplierPriceBreakColumns({
  units
}: Readonly<{
  units?: string;
}> = {}): TableColumn[] {
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
    return SupplierPriceBreakColumns({
      units: supplierPart?.part_detail?.units
    });
  }, [supplierPart?.part_detail?.units]);

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

  const priceBreakInfo = useMemo(() => {
    const packQuantity = supplierPart?.pack_quantity;
    const packQuantityNative = supplierPart?.pack_quantity_native ?? 1;
    const units = supplierPart?.part_detail?.units;

    if (packQuantityNative == 1) {
      return undefined;
    }

    // Pack quantity expressed in the native units of the base part
    const nativeQuantity = [formatDecimal(Number(packQuantityNative)), units]
      .filter(Boolean)
      .join(' ');

    // If the pack quantity was specified with its own units (e.g. "250 ml"),
    // also show the converted value (e.g. "0.25 litres")
    const packDescription = Number.isFinite(Number(packQuantity))
      ? nativeQuantity
      : `${packQuantity} (${nativeQuantity})`;

    return (
      <Alert color='blue' title={t`Supplier Pricing`}>
        <Stack gap='xs'>
          <Text size='sm'>
            {t`The quantity is the number of supplier packs which must be purchased for this price break to apply.`}
          </Text>
          <Text size='sm'>
            {t`The price is the cost of a single supplier pack, not the total cost for the specified quantity.`}
          </Text>
          {packQuantity && (
            <Text size='sm'>
              {t`Each supplier pack contains`} <b>{packDescription}</b>
            </Text>
          )}
        </Stack>
      </Alert>
    );
  }, [supplierPart]);

  const [selectedPriceBreak, setSelectedPriceBreak] = useState<number>(0);

  const newPriceBreak = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.supplier_part_pricing_list),
    title: t`Add Price Break`,
    fields: supplierPriceBreakFields,
    preFormContent: priceBreakInfo,
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
    preFormContent: priceBreakInfo,
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
