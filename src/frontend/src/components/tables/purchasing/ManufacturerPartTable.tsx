import { t } from '@lingui/macro';
import { ReactNode, useCallback, useMemo } from 'react';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { UserRoles } from '../../../enums/Roles';
import { useManufacturerPartFields } from '../../../forms/CompanyForms';
import { openDeleteApiForm, openEditApiForm } from '../../../functions/forms';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { Thumbnail } from '../../images/Thumbnail';
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

  const tableActions = useMemo(() => {
    // TODO: Custom actions
    return [];
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
                url: ApiPaths.manufacturer_part_list,
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
                url: ApiPaths.manufacturer_part_list,
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
      url={apiUrl(ApiPaths.manufacturer_part_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        params: {
          ...params,
          part_detail: true,
          manufacturer_detail: true
        },
        rowActions: rowActions,
        customActionGroups: tableActions
      }}
    />
  );
}
