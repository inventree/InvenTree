import { t } from '@lingui/macro';
import { SimpleGrid } from '@mantine/core';
import { useCallback, useMemo, useState } from 'react';
import {
  Bar,
  BarChart,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

import { AddItemButton } from '../../../components/buttons/AddItemButton';
import { ApiFormFieldSet } from '../../../components/forms/fields/ApiFormField';
import { formatCurrency } from '../../../defaults/formatters';
import { ApiEndpoints } from '../../../enums/ApiEndpoints';
import { UserRoles } from '../../../enums/Roles';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../../hooks/UseForm';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { TableColumn } from '../../../tables/Column';
import { InvenTreeTable } from '../../../tables/InvenTreeTable';
import { RowDeleteAction, RowEditAction } from '../../../tables/RowActions';

export default function InternalPricingPanel({ part }: { part: any }) {
  const user = useUserState();
  const table = useTable('pricing-internal');

  const priceBreakFields: ApiFormFieldSet = useMemo(() => {
    return {
      part: {
        hidden: true
      },
      quantity: {},
      price: {},
      price_currency: {}
    };
  }, []);

  const [selectedPriceBreak, setSelectedPriceBreak] = useState<number>(0);

  const newPriceBreak = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.part_pricing_internal),
    title: t`Add Price Break`,
    fields: priceBreakFields,
    initialData: {
      part: part.pk
    },
    onFormSuccess: (data: any) => {
      table.updateRecord(data);
    }
  });

  const editPriceBreak = useEditApiFormModal({
    url: apiUrl(ApiEndpoints.part_pricing_internal),
    pk: selectedPriceBreak,
    title: t`Edit Price Break`,
    fields: priceBreakFields,
    onFormSuccess: (data: any) => {
      table.updateRecord(data);
    }
  });

  const deletePriceBreak = useDeleteApiFormModal({
    url: apiUrl(ApiEndpoints.part_pricing_internal),
    pk: selectedPriceBreak,
    title: t`Delete Price Break`,
    onFormSuccess: () => {
      table.refreshTable();
    }
  });

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'quantity',
        title: t`Quantity`,
        sortable: true,
        switchable: false
      },
      {
        accessor: 'price',
        title: t`Price Break`,
        sortable: false,
        switchable: false,
        render: (record: any) => {
          return formatCurrency(record.price, {
            currency: record.price_currency
          });
        }
      }
    ];
  }, []);

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        tooltip={t`Add Price Break`}
        onClick={() => {
          newPriceBreak.open();
        }}
        hidden={!user.hasAddRole(UserRoles.part)}
      />
    ];
  }, [user]);

  const rowActions = useCallback(
    (record: any) => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.part),
          onClick: () => {
            setSelectedPriceBreak(record.pk);
            editPriceBreak.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.part),
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
      <SimpleGrid cols={2}>
        <InvenTreeTable
          tableState={table}
          url={apiUrl(ApiEndpoints.part_pricing_internal)}
          columns={columns}
          props={{
            params: {
              part: part.pk
            },
            tableActions: tableActions,
            rowActions: rowActions
          }}
        />
        <ResponsiveContainer width="100%" height={500}>
          <BarChart data={table.records}>
            <XAxis dataKey="quantity" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="price" fill="#8884d8" label={t`Price Break`} />
          </BarChart>
        </ResponsiveContainer>
      </SimpleGrid>
    </>
  );
}
