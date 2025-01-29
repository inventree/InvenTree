import { t } from '@lingui/macro';
import { BarChart } from '@mantine/charts';
import { SimpleGrid } from '@mantine/core';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '../../../components/buttons/AddItemButton';
import { tooltipFormatter } from '../../../components/charts/tooltipFormatter';
import type { ApiFormFieldSet } from '../../../components/forms/fields/ApiFormField';
import { formatCurrency } from '../../../defaults/formatters';
import type { ApiEndpoints } from '../../../enums/ApiEndpoints';
import { UserRoles } from '../../../enums/Roles';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../../hooks/UseForm';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import type { TableColumn } from '../../../tables/Column';
import { InvenTreeTable } from '../../../tables/InvenTreeTable';
import {
  type RowAction,
  RowDeleteAction,
  RowEditAction
} from '../../../tables/RowActions';
import { NoPricingData } from './PricingPanel';

export default function PriceBreakPanel({
  part,
  endpoint
}: Readonly<{
  part: any;
  endpoint: ApiEndpoints;
}>) {
  const user = useUserState();
  const table = useTable('pricinginternal');

  const priceBreakFields: ApiFormFieldSet = useMemo(() => {
    return {
      part: {
        disabled: true
      },
      quantity: {},
      price: {},
      price_currency: {}
    };
  }, []);

  const tableUrl = useMemo(() => {
    return apiUrl(endpoint);
  }, [endpoint]);

  const [selectedPriceBreak, setSelectedPriceBreak] = useState<number>(0);

  const newPriceBreak = useCreateApiFormModal({
    url: tableUrl,
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
    url: tableUrl,
    pk: selectedPriceBreak,
    title: t`Edit Price Break`,
    fields: priceBreakFields,
    onFormSuccess: (data: any) => {
      table.updateRecord(data);
    }
  });

  const deletePriceBreak = useDeleteApiFormModal({
    url: tableUrl,
    pk: selectedPriceBreak,
    title: t`Delete Price Break`,
    table: table
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
        sortable: true,
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

  const currency: string = useMemo(() => {
    if (table.records.length === 0) {
      return '';
    }
    return table.records[0].currency;
  }, [table.records]);

  return (
    <>
      {newPriceBreak.modal}
      {editPriceBreak.modal}
      {deletePriceBreak.modal}
      <SimpleGrid cols={{ base: 1, md: 2 }}>
        <InvenTreeTable
          tableState={table}
          url={tableUrl}
          columns={columns}
          props={{
            params: {
              part: part.pk
            },
            tableActions: tableActions,
            rowActions: rowActions
          }}
        />
        {table.records.length > 0 ? (
          <BarChart
            dataKey='quantity'
            data={table.records}
            series={[{ name: 'price', label: t`Price`, color: 'blue.6' }]}
            xAxisLabel={t`Quantity`}
            yAxisLabel={t`Unit Price`}
            valueFormatter={(value) => tooltipFormatter(value, currency)}
          />
        ) : (
          <NoPricingData />
        )}
      </SimpleGrid>
    </>
  );
}
