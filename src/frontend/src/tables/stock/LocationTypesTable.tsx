import { t } from '@lingui/macro';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import type { ApiFormFieldSet } from '../../components/forms/fields/ApiFormField';
import { ApiIcon } from '../../components/items/ApiIcon';
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

export default function LocationTypesTable() {
  const table = useTable('location-types');
  const user = useUserState();

  const formFields: ApiFormFieldSet = useMemo(() => {
    return {
      name: {},
      description: {},
      icon: {
        field_type: 'icon'
      }
    };
  }, []);

  const [selectedLocationType, setSelectedLocationType] = useState<number>(0);

  const newLocationType = useCreateApiFormModal({
    url: ApiEndpoints.stock_location_type_list,
    title: t`Add Location Type`,
    fields: useMemo(() => ({ ...formFields }), [formFields]),
    onFormSuccess: table.refreshTable
  });

  const editLocationType = useEditApiFormModal({
    url: ApiEndpoints.stock_location_type_list,
    pk: selectedLocationType,
    title: t`Edit Location Type`,
    fields: useMemo(() => ({ ...formFields }), [formFields]),
    onFormSuccess: (record: any) => table.updateRecord(record)
  });

  const deleteLocationType = useDeleteApiFormModal({
    url: ApiEndpoints.stock_location_type_list,
    pk: selectedLocationType,
    title: t`Delete Location Type`,
    onFormSuccess: table.refreshTable
  });

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'icon',
        title: t`Icon`,
        sortable: true,
        render: (value: any) => <ApiIcon name={value.icon} />
      },
      {
        accessor: 'name',
        title: t`Name`,
        sortable: true
      },
      {
        accessor: 'description',
        title: t`Description`
      },
      {
        accessor: 'location_count',
        sortable: true
      }
    ];
  }, []);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.stock_location),
          onClick: () => {
            setSelectedLocationType(record.pk);
            editLocationType.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.stock_location),
          onClick: () => {
            setSelectedLocationType(record.pk);
            deleteLocationType.open();
          }
        })
      ];
    },
    [user]
  );

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-location-type'
        tooltip={t`Add Location Type`}
        onClick={() => newLocationType.open()}
        hidden={!user.hasAddRole(UserRoles.stock_location)}
      />
    ];
  }, [user]);

  return (
    <>
      {newLocationType.modal}
      {editLocationType.modal}
      {deleteLocationType.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.stock_location_type_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          rowActions: rowActions,
          tableActions: tableActions
        }}
      />
    </>
  );
}
