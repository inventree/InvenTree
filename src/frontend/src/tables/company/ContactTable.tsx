import { t } from '@lingui/macro';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
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
import { InvenTreeTable } from '../InvenTreeTable';
import { type RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

export function ContactTable({
  companyId,
  params
}: Readonly<{
  companyId: number;
  params?: any;
}>) {
  const user = useUserState();

  const table = useTable('contact');

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        sortable: true,
        switchable: false
      },
      {
        accessor: 'phone',
        switchable: true,
        sortable: false
      },
      {
        accessor: 'email',
        switchable: true,
        sortable: false
      },
      {
        accessor: 'role',
        switchable: true,
        sortable: false
      }
    ];
  }, []);

  const contactFields: ApiFormFieldSet = useMemo(() => {
    return {
      company: {},
      name: {},
      phone: {},
      email: {},
      role: {}
    };
  }, []);

  const [selectedContact, setSelectedContact] = useState<number>(0);

  const editContact = useEditApiFormModal({
    url: ApiEndpoints.contact_list,
    pk: selectedContact,
    title: t`Edit Contact`,
    fields: contactFields,
    onFormSuccess: (record: any) => table.updateRecord(record)
  });

  const newContact = useCreateApiFormModal({
    url: ApiEndpoints.contact_list,
    title: t`Add Contact`,
    initialData: {
      company: companyId
    },
    fields: contactFields,
    table: table
  });

  const deleteContact = useDeleteApiFormModal({
    url: ApiEndpoints.contact_list,
    pk: selectedContact,
    title: t`Delete Contact`,
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
            setSelectedContact(record.pk);
            editContact.open();
          }
        }),
        RowDeleteAction({
          hidden: !can_delete,
          onClick: () => {
            setSelectedContact(record.pk);
            deleteContact.open();
          }
        })
      ];
    },
    [user]
  );

  const tableActions = useMemo(() => {
    const can_add =
      user.hasAddRole(UserRoles.purchase_order) ||
      user.hasAddRole(UserRoles.sales_order);

    return [
      <AddItemButton
        key='add-contact'
        tooltip={t`Add contact`}
        onClick={() => newContact.open()}
        hidden={!can_add}
      />
    ];
  }, [user]);

  return (
    <>
      {newContact.modal}
      {editContact.modal}
      {deleteContact.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.contact_list)}
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
