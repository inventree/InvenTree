import { t } from '@lingui/core/macro';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import {
  type RowAction,
  RowDeleteAction,
  RowEditAction
} from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { getDetailUrl } from '@lib/functions/Navigation';
import useTable from '@lib/hooks/UseTable';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import type { TableColumn } from '@lib/types/Tables';
import { useNavigate } from 'react-router-dom';
import { ApiIcon } from '../../components/items/ApiIcon';
import { RenderInlineModel } from '../../components/render/Instance';
import { DescriptionColumn } from '../../components/tables/ColumnRenderers';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useUserState } from '../../states/UserState';

export default function LocationTypesTable() {
  const table = useTable('location-types');
  const user = useUserState();
  const navigate = useNavigate();

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
        sortable: true,
        render: (record) => (
          <RenderInlineModel
            primary={record.name}
            url={getDetailUrl(ModelType.stocklocationtype, record.pk)}
            navigate={navigate}
          />
        )
      },
      DescriptionColumn({}),
      {
        accessor: 'location_count',
        sortable: true
      }
    ];
  }, [navigate]);

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
