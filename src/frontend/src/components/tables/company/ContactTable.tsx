import { t } from '@lingui/macro';
import { Text } from '@mantine/core';
import { useCallback, useMemo } from 'react';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { UserRoles } from '../../../enums/Roles';
import { contactFields } from '../../../forms/CompanyForms';
import {
  openCreateApiForm,
  openDeleteApiForm,
  openEditApiForm
} from '../../../functions/forms';
import { useTableRefresh } from '../../../hooks/TableRefresh';
import { apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { AddItemButton } from '../../buttons/AddItemButton';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowDeleteAction, RowEditAction } from '../RowActions';

export function ContactTable({
  companyId,
  params
}: {
  companyId: number;
  params?: any;
}) {
  const user = useUserState();

  const { tableKey, refreshTable } = useTableRefresh('contact');

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Name`,
        sortable: true,
        switchable: false
      },
      {
        accessor: 'phone',
        title: t`Phone`,
        switchable: true,
        sortable: false
      },
      {
        accessor: 'email',
        title: t`Email`,
        switchable: true,
        sortable: false
      },
      {
        accessor: 'notes',
        title: t`Notes`,
        switchable: true,
        sortable: false
      },
      {
        accessor: 'role',
        title: t`Role`,
        switchable: true,
        sortable: false
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
              url: ApiPaths.contact_list,
              pk: record.pk,
              title: t`Edit Contact`,
              fields: contactFields(),
              successMessage: t`Contact updated`,
              onFormSuccess: refreshTable
            });
          }
        }),
        RowDeleteAction({
          hidden: !can_delete,
          onClick: () => {
            openDeleteApiForm({
              url: ApiPaths.contact_list,
              pk: record.pk,
              title: t`Delete Contact`,
              successMessage: t`Contact deleted`,
              onFormSuccess: refreshTable,
              preFormContent: <Text>{t`Remove contact`}</Text>
            });
          }
        })
      ];
    },
    [user]
  );

  const addContact = useCallback(() => {
    var fields = contactFields();

    fields['company'].value = companyId;

    openCreateApiForm({
      url: ApiPaths.contact_list,
      title: t`Create Contact`,
      fields: fields,
      successMessage: t`Contact created`,
      onFormSuccess: refreshTable
    });
  }, [companyId]);

  const tableActions = useMemo(() => {
    let can_add =
      user.hasAddRole(UserRoles.purchase_order) ||
      user.hasAddRole(UserRoles.sales_order);

    return [
      <AddItemButton
        tooltip={t`Add contact`}
        onClick={addContact}
        disabled={!can_add}
      />
    ];
  }, [user]);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.contact_list)}
      tableKey={tableKey}
      columns={columns}
      props={{
        rowActions: rowActions,
        customActionGroups: tableActions,
        params: {
          ...params,
          company: companyId
        }
      }}
    />
  );
}
