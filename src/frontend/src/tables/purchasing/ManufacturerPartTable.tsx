import { t } from '@lingui/macro';
import { ReactNode, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { Thumbnail } from '../../components/images/Thumbnail';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { useManufacturerPartFields } from '../../forms/CompanyForms';
import { openDeleteApiForm, openEditApiForm } from '../../functions/forms';
import { notYetImplemented } from '../../functions/notifications';
import { getDetailUrl } from '../../functions/urls';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { DescriptionColumn, LinkColumn, PartColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowDeleteAction, RowEditAction } from '../RowActions';

/*
 * Construct a table listing manufacturer parts
 */
export function ManufacturerPartTable({ params }: { params: any }): ReactNode {
  const table = useTable('manufacturerparts');

  const user = useUserState();
  const navigate = useNavigate();

  // Construct table columns for this table
  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'part',
        title: t`Part`,
        switchable: 'part' in params,
        sortable: true,
        render: (record: any) => PartColumn(record?.part_detail)
      },
      {
        accessor: 'manufacturer',
        title: t`Manufacturer`,
        sortable: true,
        render: (record: any) => {
          let manufacturer = record?.manufacturer_detail ?? {};

          return (
            <Thumbnail
              src={manufacturer?.thumbnail ?? manufacturer.image}
              text={manufacturer.name}
            />
          );
        }
      },
      {
        accessor: 'MPN',
        title: t`Manufacturer Part Number`,
        sortable: true
      },
      DescriptionColumn({}),
      LinkColumn()
    ];
  }, [params]);

  const addManufacturerPart = useCallback(() => {
    notYetImplemented();
  }, []);

  const tableActions = useMemo(() => {
    let can_add =
      user.hasAddRole(UserRoles.purchase_order) &&
      user.hasAddRole(UserRoles.part);

    return [
      <AddItemButton
        tooltip={t`Add Manufacturer Part`}
        onClick={addManufacturerPart}
        hidden={!can_add}
      />
    ];
  }, [user]);

  const editManufacturerPartFields = useManufacturerPartFields();

  const rowActions = useCallback(
    (record: any) => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.purchase_order),
          onClick: () => {
            record.pk &&
              openEditApiForm({
                url: ApiEndpoints.manufacturer_part_list,
                pk: record.pk,
                title: t`Edit Manufacturer Part`,
                fields: editManufacturerPartFields,
                onFormSuccess: table.refreshTable,
                successMessage: t`Manufacturer part updated`
              });
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.purchase_order),
          onClick: () => {
            record.pk &&
              openDeleteApiForm({
                url: ApiEndpoints.manufacturer_part_list,
                pk: record.pk,
                title: t`Delete Manufacturer Part`,
                successMessage: t`Manufacturer part deleted`,
                onFormSuccess: table.refreshTable,
                preFormWarning: t`Are you sure you want to remove this manufacturer part?`
              });
          }
        })
      ];
    },
    [user]
  );

  return (
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
        rowActions: rowActions,
        tableActions: tableActions,
        onRowClick: (record: any) => {
          if (record?.pk) {
            navigate(getDetailUrl(ModelType.manufacturerpart, record.pk));
          }
        }
      }}
    />
  );
}
