import { t } from '@lingui/core/macro';
import { type ReactNode, useCallback, useMemo, useState } from 'react';

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
import type { TableColumn } from '@lib/types/Tables';
import { useManufacturerPartFields } from '../../forms/CompanyForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import {
  CompanyColumn,
  DescriptionColumn,
  LinkColumn,
  PartColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

/*
 * Construct a table listing manufacturer parts
 */
export function ManufacturerPartTable({
  params
}: Readonly<{ params: any }>): ReactNode {
  const table = useTable('manufacturerparts');

  const user = useUserState();

  // Construct table columns for this table
  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      PartColumn({
        switchable: 'part' in params
      }),
      {
        accessor: 'manufacturer',
        sortable: true,
        render: (record: any) => (
          <CompanyColumn company={record?.manufacturer_detail} />
        )
      },
      {
        accessor: 'MPN',
        title: t`MPN`,
        sortable: true
      },
      DescriptionColumn({}),
      LinkColumn({})
    ];
  }, [params]);

  const manufacturerPartFields = useManufacturerPartFields();

  const [selectedPart, setSelectedPart] = useState<number | undefined>(
    undefined
  );

  const createManufacturerPart = useCreateApiFormModal({
    url: ApiEndpoints.manufacturer_part_list,
    title: t`Add Manufacturer Part`,
    fields: manufacturerPartFields,
    table: table,
    initialData: {
      manufacturer: params?.manufacturer,
      part: params?.part
    }
  });

  const editManufacturerPart = useEditApiFormModal({
    url: ApiEndpoints.manufacturer_part_list,
    pk: selectedPart,
    title: t`Edit Manufacturer Part`,
    fields: manufacturerPartFields,
    table: table
  });

  const deleteManufacturerPart = useDeleteApiFormModal({
    url: ApiEndpoints.manufacturer_part_list,
    pk: selectedPart,
    title: t`Delete Manufacturer Part`,
    table: table
  });

  const tableActions = useMemo(() => {
    const can_add =
      user.hasAddRole(UserRoles.purchase_order) &&
      user.hasAddRole(UserRoles.part);

    return [
      <AddItemButton
        key='add-manufacturer-part'
        tooltip={t`Add Manufacturer Part`}
        onClick={() => createManufacturerPart.open()}
        hidden={!can_add}
      />
    ];
  }, [user]);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.purchase_order),
          onClick: () => {
            setSelectedPart(record.pk);
            editManufacturerPart.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.purchase_order),
          onClick: () => {
            setSelectedPart(record.pk);
            deleteManufacturerPart.open();
          }
        })
      ];
    },
    [user]
  );

  return (
    <>
      {createManufacturerPart.modal}
      {editManufacturerPart.modal}
      {deleteManufacturerPart.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.manufacturer_part_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            ...params,
            part_detail: true,
            manufacturer_detail: true
          },
          enableDownload: true,
          rowActions: rowActions,
          tableActions: tableActions,
          modelType: ModelType.manufacturerpart
        }}
      />
    </>
  );
}
