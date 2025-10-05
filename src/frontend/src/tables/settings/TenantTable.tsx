import { t } from '@lingui/core/macro';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import { RowDeleteAction, RowEditAction } from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { RowAction, TableColumn } from '@lib/types/Tables';
import { tenantFields } from '../../forms/TenantForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import { BooleanColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * Table for displaying list of tenants
 */
export default function TenantTable() {
  const table = useTable('tenants');

  const user = useUserState();

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        sortable: true,
        title: t`Name`
      },
      {
        accessor: 'code',
        sortable: true,
        title: t`Code`
      },
      {
        accessor: 'description',
        sortable: false,
        title: t`Description`
      },
      BooleanColumn({
        accessor: 'is_active',
        title: t`Active`
      }),
      {
        accessor: 'contact_name',
        sortable: false,
        title: t`Contact Name`
      },
      {
        accessor: 'contact_email',
        sortable: false,
        title: t`Contact Email`
      },
      {
        accessor: 'contact_phone',
        sortable: false,
        title: t`Contact Phone`
      }
    ];
  }, []);

  const newTenant = useCreateApiFormModal({
    url: ApiEndpoints.tenant_list,
    title: t`Add Tenant`,
    fields: tenantFields(),
    table: table
  });

  const [selectedTenant, setSelectedTenant] = useState<number | undefined>(
    undefined
  );

  const editTenant = useEditApiFormModal({
    url: ApiEndpoints.tenant_list,
    pk: selectedTenant,
    title: t`Edit Tenant`,
    fields: tenantFields(),
    table: table
  });

  const deleteTenant = useDeleteApiFormModal({
    url: ApiEndpoints.tenant_list,
    pk: selectedTenant,
    title: t`Delete Tenant`,
    table: table
  });

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.admin),
          onClick: () => {
            setSelectedTenant(record.pk);
            editTenant.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.admin),
          onClick: () => {
            setSelectedTenant(record.pk);
            deleteTenant.open();
          }
        })
      ];
    },
    [user, editTenant, deleteTenant]
  );

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add'
        onClick={() => newTenant.open()}
        tooltip={t`Add tenant`}
        hidden={!user.hasAddRole(UserRoles.admin)}
      />
    ];
  }, [user, newTenant]);

  return (
    <>
      {newTenant.modal}
      {editTenant.modal}
      {deleteTenant.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.tenant_list)}
        tableState={table}
        columns={columns}
        props={{
          rowActions: rowActions,
          tableActions: tableActions,
          enableSelection: true,
          enableSearch: true,
          enableFilters: true,
          enablePagination: true,
          enableColumnSwitching: true
        }}
      />
    </>
  );
}
