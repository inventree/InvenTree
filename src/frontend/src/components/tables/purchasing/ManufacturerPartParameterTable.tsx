import { faL } from '@fortawesome/free-solid-svg-icons';
import { t } from '@lingui/macro';
import { useCallback, useMemo } from 'react';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { UserRoles } from '../../../enums/Roles';
import { useManufacturerPartParameterFields } from '../../../forms/CompanyForms';
import { openDeleteApiForm, openEditApiForm } from '../../../functions/forms';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowDeleteAction, RowEditAction } from '../RowActions';

export default function ManufacturerPartParameterTable({
  params
}: {
  params: any;
}) {
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

  const rowActions = useCallback(
    (record: any) => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.purchase_order),
          onClick: () => {
            openEditApiForm({
              url: ApiPaths.manufacturer_part_parameter_list,
              pk: record.pk,
              title: t`Edit Parameter`,
              fields: fields,
              onFormSuccess: table.refreshTable,
              successMessage: t`Parameter updated`
            });
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.purchase_order),
          onClick: () => {
            record.pk &&
              openDeleteApiForm({
                url: ApiPaths.manufacturer_part_parameter_list,
                pk: record.pk,
                title: t`Delete Parameter`,
                onFormSuccess: table.refreshTable,
                successMessage: t`Parameter deleted`,
                preFormWarning: t`Are you sure you want to delete this parameter?`
              });
          }
        })
      ];
    },
    [user]
  );

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.manufacturer_part_parameter_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        params: {
          ...params
        },
        rowActions: rowActions
      }}
    />
  );
}
