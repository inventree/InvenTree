import { t } from '@lingui/macro';
import { useCallback, useMemo, useState } from 'react';

import { formatPriceRange } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import { partStocktakeFields } from '../../forms/PartForms';
import {
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowDeleteAction, RowEditAction } from '../RowActions';

export default function PartStocktakeTable({ partId }: { partId: number }) {
  const user = useUserState();
  const table = useTable('part-stocktake');

  const stocktakeFields = useMemo(() => partStocktakeFields(), []);

  const [selectedStocktake, setSelectedStocktake] = useState<
    number | undefined
  >(undefined);

  const editStocktakeEntry = useEditApiFormModal({
    pk: selectedStocktake,
    url: ApiEndpoints.part_stocktake_list,
    title: t`Edit Stocktake Entry`,
    fields: stocktakeFields,
    table: table
  });

  const deleteStocktakeEntry = useDeleteApiFormModal({
    pk: selectedStocktake,
    url: ApiEndpoints.part_stocktake_list,
    title: t`Delete Stocktake Entry`,
    table: table
  });

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'quantity',
        sortable: true,
        switchable: false
      },
      {
        accessor: 'item_count',
        switchable: true,
        sortable: true
      },
      {
        accessor: 'cost',
        title: t`Stock Value`,
        render: (record: any) => {
          return formatPriceRange(record.cost_min, record.cost_max, {
            currency: record.cost_min_currency
          });
        }
      },
      {
        accessor: 'date',
        sortable: true
      },
      {
        accessor: 'note'
      }
    ];
  }, []);

  const tableActions = useMemo(() => {
    return [];
  }, []);

  const rowActions = useCallback(
    (record: any) => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.part),
          onClick: () => {
            setSelectedStocktake(record.pk);
            editStocktakeEntry.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.part),
          onClick: () => {
            setSelectedStocktake(record.pk);
            deleteStocktakeEntry.open();
          }
        })
      ];
    },
    [user]
  );

  return (
    <>
      {editStocktakeEntry.modal}
      {deleteStocktakeEntry.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.part_stocktake_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            part: partId
          },
          rowActions: rowActions,
          tableActions: tableActions
        }}
      />
    </>
  );
}
