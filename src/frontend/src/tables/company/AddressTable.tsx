import { t } from '@lingui/macro';
import { useCallback, useMemo } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { YesNoButton } from '../../components/items/YesNoButton';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import { addressFields } from '../../forms/CompanyForms';
import {
  openCreateApiForm,
  openDeleteApiForm,
  openEditApiForm
} from '../../functions/forms';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowDeleteAction, RowEditAction } from '../RowActions';

export function AddressTable({
  companyId,
  params
}: {
  companyId: number;
  params?: any;
}) {
  const user = useUserState();

  const table = useTable('address');

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'title',
        title: t`Title`,
        sortable: true,
        switchable: false
      },
      {
        accessor: 'primary',
        title: t`Primary`,
        switchable: false,
        sortable: false,
        render: (record: any) => YesNoButton({ value: record.primary })
      },
      {
        accessor: 'address',
        title: t`Address`,
        sortable: false,
        switchable: false,
        render: (record: any) => {
          let address = '';

          if (record?.line1) {
            address += record.line1;
          }

          if (record?.line2) {
            address += ' ' + record.line2;
          }

          return address.trim();
        }
      },
      {
        accessor: 'postal_code',
        title: t`Postal Code`,
        sortable: false,
        switchable: true
      },
      {
        accessor: 'postal_city',
        title: t`City`,
        sortable: false,
        switchable: true
      },
      {
        accessor: 'province',
        title: t`State / Province`,
        sortable: false,
        switchable: true
      },
      {
        accessor: 'country',
        title: t`Country`,
        sortable: false,
        switchable: true
      },
      {
        accessor: 'shipping_notes',
        title: t`Courier Notes`,
        sortable: false,
        switchable: true
      },
      {
        accessor: 'internal_shipping_notes',
        title: t`Internal Notes`,
        sortable: false,
        switchable: true
      },
      {
        accessor: 'link',
        title: t`Link`,
        sortable: false,
        switchable: true
      }
    ];
  }, []);

  const rowActions = useCallback(
    (record: any) => {
      let can_edit =
        user.hasChangeRole(UserRoles.purchase_order) ||
        user.hasChangeRole(UserRoles.sales_order);

      let can_delete =
        user.hasDeleteRole(UserRoles.purchase_order) ||
        user.hasDeleteRole(UserRoles.sales_order);

      return [
        RowEditAction({
          hidden: !can_edit,
          onClick: () => {
            openEditApiForm({
              url: ApiEndpoints.address_list,
              pk: record.pk,
              title: t`Edit Address`,
              fields: addressFields(),
              successMessage: t`Address updated`,
              onFormSuccess: table.refreshTable
            });
          }
        }),
        RowDeleteAction({
          hidden: !can_delete,
          onClick: () => {
            openDeleteApiForm({
              url: ApiEndpoints.address_list,
              pk: record.pk,
              title: t`Delete Address`,
              successMessage: t`Address deleted`,
              onFormSuccess: table.refreshTable,
              preFormWarning: t`Are you sure you want to delete this address?`
            });
          }
        })
      ];
    },
    [user]
  );

  const addAddress = useCallback(() => {
    let fields = addressFields();

    fields['company'].value = companyId;

    openCreateApiForm({
      url: ApiEndpoints.address_list,
      title: t`Add Address`,
      fields: fields,
      successMessage: t`Address created`,
      onFormSuccess: table.refreshTable
    });
  }, [companyId]);

  const tableActions = useMemo(() => {
    let can_add =
      user.hasChangeRole(UserRoles.purchase_order) ||
      user.hasChangeRole(UserRoles.sales_order);

    return [
      <AddItemButton
        tooltip={t`Add Address`}
        onClick={addAddress}
        disabled={!can_add}
      />
    ];
  }, [user]);

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.address_list)}
      tableState={table}
      columns={columns}
      props={{
        rowActions: rowActions,
        tableActions: tableActions,
        params: {
          ...params,
          company: companyId
        }
      }}
    />
  );
}
