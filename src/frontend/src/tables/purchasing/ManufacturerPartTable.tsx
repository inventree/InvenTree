import { t } from '@lingui/core/macro';
import { type ReactNode, useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import {
  type RowAction,
  RowDeleteAction,
  RowDuplicateAction,
  RowEditAction
} from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
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
  manufacturerId,
  partId
}: Readonly<{
  manufacturerId?: number;
  partId?: number;
}>): ReactNode {
  const tableId: string = useMemo(() => {
    let tId = 'manufacturer-part';

    if (manufacturerId) {
      tId += '-manufacturer';
    }

    if (partId) {
      tId += '-part';
    }

    return tId;
  }, [manufacturerId, partId]);

  const table = useTable(tableId);

  const user = useUserState();

  // Construct table columns for this table
  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      PartColumn({
        switchable: !!partId
      }),
      {
        accessor: 'part_detail.IPN',
        title: t`IPN`,
        sortable: false,
        switchable: true
      },
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
  }, [partId]);

  const manufacturerPartFields = useManufacturerPartFields();

  const [selectedPart, setSelectedPart] = useState<any>(undefined);

  const createManufacturerPart = useCreateApiFormModal({
    url: ApiEndpoints.manufacturer_part_list,
    title: t`Add Manufacturer Part`,
    fields: manufacturerPartFields,
    table: table,
    initialData: {
      manufacturer: manufacturerId,
      part: partId
    }
  });

  const editManufacturerPart = useEditApiFormModal({
    url: ApiEndpoints.manufacturer_part_list,
    pk: selectedPart?.pk,
    title: t`Edit Manufacturer Part`,
    fields: useMemo(() => manufacturerPartFields, [manufacturerPartFields]),
    table: table
  });

  const duplicateManufacturerPart = useCreateApiFormModal({
    url: ApiEndpoints.manufacturer_part_list,
    title: t`Add Manufacturer Part`,
    fields: useMemo(() => manufacturerPartFields, [manufacturerPartFields]),
    table: table,
    initialData: {
      ...selectedPart
    }
  });

  const deleteManufacturerPart = useDeleteApiFormModal({
    url: ApiEndpoints.manufacturer_part_list,
    pk: selectedPart?.pk,
    title: t`Delete Manufacturer Part`,
    table: table
  });

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'part_active',
        label: t`Active Part`,
        description: t`Show manufacturer parts for active internal parts.`,
        type: 'boolean'
      },
      {
        name: 'manufacturer_active',
        label: t`Active Manufacturer`,
        active: !manufacturerId,
        description: t`Show manufacturer parts for active manufacturers.`,
        type: 'boolean'
      }
    ];
  }, [manufacturerId]);

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
            setSelectedPart(record);
            editManufacturerPart.open();
          }
        }),
        RowDuplicateAction({
          hidden: !user.hasAddRole(UserRoles.purchase_order),
          onClick: () => {
            setSelectedPart(record);
            duplicateManufacturerPart.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.purchase_order),
          onClick: () => {
            setSelectedPart(record);
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
      {duplicateManufacturerPart.modal}
      {editManufacturerPart.modal}
      {deleteManufacturerPart.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.manufacturer_part_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            part: partId,
            manufacturer: manufacturerId,
            part_detail: true,
            manufacturer_detail: true
          },
          enableDownload: true,
          rowActions: rowActions,
          tableActions: tableActions,
          tableFilters: tableFilters,
          modelType: ModelType.manufacturerpart
        }}
      />
    </>
  );
}
