import { t } from '@lingui/macro';
import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { YesNoButton } from '../../components/items/YesNoButton';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { stockLocationFields } from '../../forms/StockForms';
import { openCreateApiForm, openEditApiForm } from '../../functions/forms';
import { getDetailUrl } from '../../functions/urls';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { DescriptionColumn } from '../ColumnRenderers';
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
        label: t`Structural`,
        description: t`Show structural locations`
      },
      {
        name: 'external',
        label: t`External`,
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
      {
        accessor: 'structural',
        sortable: true,
        render: (record: any) => <YesNoButton value={record.structural} />
      },
      {
        accessor: 'external',
        sortable: true,
        render: (record: any) => <YesNoButton value={record.external} />
      },
      {
        accessor: 'location_type',
        sortable: false,
        render: (record: any) => record.location_type_detail?.name
      }
    ];
  }, []);

  const addLocation = useCallback(() => {
    let fields = stockLocationFields({});

    if (parentId) {
      fields['parent'].value = parentId;
    }

    openCreateApiForm({
      url: apiUrl(ApiEndpoints.stock_location_list),
      title: t`Add Stock Location`,
      fields: fields,
      onFormSuccess(data: any) {
        if (data.pk) {
          navigate(`/stock/location/${data.pk}`);
        } else {
          table.refreshTable();
        }
      }
    });
  }, [parentId]);

  const tableActions = useMemo(() => {
    let can_add = user.hasAddRole(UserRoles.stock_location);

    return [
      <AddItemButton
        tooltip={t`Add Stock Location`}
        onClick={addLocation}
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
            openEditApiForm({
              url: ApiEndpoints.stock_location_list,
              pk: record.pk,
              title: t`Edit Stock Location`,
              fields: stockLocationFields({}),
              successMessage: t`Stock location updated`,
              onFormSuccess: table.refreshTable
            });
          }
        })
      ];
    },
    [user]
  );

  return (
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
        // TODO: allow for "tree view" with cascade
      }}
    />
  );
}
