import { t } from '@lingui/macro';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { ApiFormFieldSet } from '../../components/forms/fields/ApiFormField';
import { YesNoButton } from '../../components/items/YesNoButton';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
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
        sortable: true,
        switchable: false
      },
      {
        accessor: 'primary',
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
        sortable: false,
        switchable: true
      },
      {
        accessor: 'postal_city',
        sortable: false,
        switchable: true
      },
      {
        accessor: 'province',
        sortable: false,
        switchable: true
      },
      {
        accessor: 'country',
        sortable: false,
        switchable: true
      },
      {
        accessor: 'shipping_notes',
        sortable: false,
        switchable: true
      },
      {
        accessor: 'internal_shipping_notes',
        sortable: false,
        switchable: true
      },
      {
        accessor: 'link',
        sortable: false,
        switchable: true
      }
    ];
  }, []);

  const addressFields: ApiFormFieldSet = useMemo(() => {
    return {
      company: {},
      title: {},
      primary: {},
      line1: {},
      line2: {},
      postal_code: {},
      postal_city: {},
      province: {},
      country: {},
      shipping_notes: {},
      internal_shipping_notes: {},
      link: {}
    };
  }, []);

  const newAddress = useCreateApiFormModal({
    url: ApiEndpoints.address_list,
    title: t`Add Address`,
    fields: addressFields,
    initialData: {
      company: companyId
    },
    successMessage: t`Address created`,
    onFormSuccess: table.refreshTable
  });

  const [selectedAddress, setSelectedAddress] = useState<number>(-1);

  const editAddress = useEditApiFormModal({
    url: ApiEndpoints.address_list,
    pk: selectedAddress,
    title: t`Edit Address`,
    fields: addressFields,
    onFormSuccess: (record: any) => table.updateRecord(record)
  });

  const deleteAddress = useDeleteApiFormModal({
    url: ApiEndpoints.address_list,
    pk: selectedAddress,
    title: t`Delete Address`,
    onFormSuccess: table.refreshTable,
    preFormWarning: t`Are you sure you want to delete this address?`
  });

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
            setSelectedAddress(record.pk);
            editAddress.open();
          }
        }),
        RowDeleteAction({
          hidden: !can_delete,
          onClick: () => {
            setSelectedAddress(record.pk);
            deleteAddress.open();
          }
        })
      ];
    },
    [user]
  );

  const tableActions = useMemo(() => {
    let can_add =
      user.hasChangeRole(UserRoles.purchase_order) ||
      user.hasChangeRole(UserRoles.sales_order);

    return [
      <AddItemButton
        tooltip={t`Add Address`}
        onClick={() => newAddress.open()}
        disabled={!can_add}
      />
    ];
  }, [user]);

  return (
    <>
      {newAddress.modal}
      {editAddress.modal}
      {deleteAddress.modal}
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
    </>
  );
}
