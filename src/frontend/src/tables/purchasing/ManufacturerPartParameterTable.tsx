import { t } from '@lingui/core/macro';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '@lib/components/buttons/AddItemButton';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '@lib/forms';
import { apiUrl } from '@lib/functions';
import { useTable } from '@lib/hooks';
import { ApiEndpoints } from '@lib/index';
import { UserRoles } from '@lib/index';
import { useUserState } from '@lib/index';
import type { RowAction, TableColumn } from '@lib/tables';
import { RowDeleteAction, RowEditAction } from '@lib/tables';
import { InvenTreeTable } from '../../../lib/tables/InvenTreeTable';
import { useManufacturerPartParameterFields } from '../../forms/CompanyForms';

export default function ManufacturerPartParameterTable({
  params
}: Readonly<{
  params: any;
}>) {
  const table = useTable('manufacturer-part-parameter');
  const user = useUserState();

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Name`,
        sortable: true,
        switchable: false
      },
      {
        accessor: 'value',
        title: t`Value`,
        sortable: true,
        switchable: false
      },
      {
        accessor: 'units',
        title: t`Units`,
        sortable: false,
        switchable: true
      }
    ];
  }, []);

  const fields = useManufacturerPartParameterFields();

  const [selectedParameter, setSelectedParameter] = useState<
    number | undefined
  >(undefined);

  const createParameter = useCreateApiFormModal({
    url: ApiEndpoints.manufacturer_part_parameter_list,
    title: t`Add Parameter`,
    fields: fields,
    table: table,
    initialData: {
      manufacturer_part: params.manufacturer_part
    }
  });

  const editParameter = useEditApiFormModal({
    url: ApiEndpoints.manufacturer_part_parameter_list,
    pk: selectedParameter,
    title: t`Edit Parameter`,
    fields: fields,
    table: table
  });

  const deleteParameter = useDeleteApiFormModal({
    url: ApiEndpoints.manufacturer_part_parameter_list,
    pk: selectedParameter,
    title: t`Delete Parameter`,
    table: table
  });

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.purchase_order),
          onClick: () => {
            setSelectedParameter(record.pk);
            editParameter.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.purchase_order),
          onClick: () => {
            setSelectedParameter(record.pk);
            deleteParameter.open();
          }
        })
      ];
    },
    [user]
  );

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-parameter'
        tooltip={t`Add Parameter`}
        onClick={() => {
          createParameter.open();
        }}
        hidden={!user.hasAddRole(UserRoles.purchase_order)}
      />
    ];
  }, [user]);

  return (
    <>
      {createParameter.modal}
      {editParameter.modal}
      {deleteParameter.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.manufacturer_part_parameter_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            ...params
          },
          rowActions: rowActions,
          tableActions: tableActions
        }}
      />
    </>
  );
}
