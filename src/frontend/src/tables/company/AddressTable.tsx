import { t } from '@lingui/macro';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { YesNoButton } from '../../components/buttons/YesNoButton';
import type { ApiFormFieldSet } from '../../components/forms/fields/ApiFormField';
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
import type { TableColumn } from '../Column';
import { LinkColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { type RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

export function AddressTable({
  companyId,
  params
}: Readonly<{
  companyId: number;
  params?: any;
}>) {
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
            address += ` ${record.line2}`;
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
      LinkColumn({})
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
    table: table
  });

  const [selectedAddress, setSelectedAddress] = useState<number>(-1);

  const editAddress = useEditApiFormModal({
    url: ApiEndpoints.address_list,
    pk: selectedAddress,
    title: t`Edit Address`,
    fields: addressFields,
    table: table
  });

  const deleteAddress = useDeleteApiFormModal({
    url: ApiEndpoints.address_list,
    pk: selectedAddress,
    title: t`Delete Address`,
    preFormWarning: t`Are you sure you want to delete this address?`,
    table: table
  });

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      const can_edit =
        user.hasChangeRole(UserRoles.purchase_order) ||
        user.hasChangeRole(UserRoles.sales_order);

      const can_delete =
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
    const can_add =
      user.hasChangeRole(UserRoles.purchase_order) ||
      user.hasChangeRole(UserRoles.sales_order);

    return [
      <AddItemButton
        key='add-address'
        tooltip={t`Add Address`}
        onClick={() => newAddress.open()}
        hidden={!can_add}
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
          enableDownload: true,
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
