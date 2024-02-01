import { t } from '@lingui/macro';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { YesNoButton } from '../../components/items/YesNoButton';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { stockLocationFields } from '../../forms/StockForms';
import { getDetailUrl } from '../../functions/urls';
import {
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { BooleanColumn, DescriptionColumn } from '../ColumnRenderers';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowEditAction } from '../RowActions';

/**
 * Stock location table
 */
export function StockLocationTable({ parentId }: { parentId?: any }) {
  const table = useTable('stocklocation');
  const user = useUserState();

  const navigate = useNavigate();

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'cascade',
        label: t`Include Sublocations`,
        description: t`Include sublocations in results`
      },
      {
        name: 'structural',
        description: t`Show structural locations`
      },
      {
        name: 'external',
        description: t`Show external locations`
      },
      {
        name: 'has_location_type',
        label: t`Has location type`
      }
      // TODO: location_type
    ];
  }, []);

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        switchable: false
      },
      DescriptionColumn({}),
      {
        accessor: 'pathstring',
        sortable: true
      },
      {
        accessor: 'items',
        sortable: true
      },
      BooleanColumn({
        accessor: 'structural'
      }),
      BooleanColumn({
        accessor: 'external'
      }),
      {
        accessor: 'location_type',
        sortable: false,
        render: (record: any) => record.location_type_detail?.name
      }
    ];
  }, []);

  const newLocation = useCreateApiFormModal({
    url: ApiEndpoints.stock_location_list,
    title: t`Add Stock Location`,
    fields: stockLocationFields({}),
    initialData: {
      parent: parentId
    },
    onFormSuccess(data: any) {
      if (data.pk) {
        navigate(getDetailUrl(ModelType.stocklocation, data.pk));
      } else {
        table.refreshTable();
      }
    }
  });

  const [selectedLocation, setSelectedLocation] = useState<number | undefined>(
    undefined
  );

  const editLocation = useEditApiFormModal({
    url: ApiEndpoints.stock_location_list,
    pk: selectedLocation,
    title: t`Edit Stock Location`,
    fields: stockLocationFields({}),
    onFormSuccess: table.refreshTable
  });

  const tableActions = useMemo(() => {
    let can_add = user.hasAddRole(UserRoles.stock_location);

    return [
      <AddItemButton
        tooltip={t`Add Stock Location`}
        onClick={() => newLocation.open()}
        disabled={!can_add}
      />
    ];
  }, [user]);

  const rowActions = useCallback(
    (record: any) => {
      let can_edit = user.hasChangeRole(UserRoles.stock_location);

      return [
        RowEditAction({
          hidden: !can_edit,
          onClick: () => {
            setSelectedLocation(record.pk);
            editLocation.open();
          }
        })
      ];
    },
    [user]
  );

  return (
    <>
      {newLocation.modal}
      {editLocation.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.stock_location_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          enableDownload: true,
          params: {
            parent: parentId ?? 'null'
          },
          tableFilters: tableFilters,
          tableActions: tableActions,
          rowActions: rowActions,
          onRowClick: (record) => {
            navigate(getDetailUrl(ModelType.stocklocation, record.pk));
          }
        }}
      />
    </>
  );
}
