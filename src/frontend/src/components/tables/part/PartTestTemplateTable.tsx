import { t } from '@lingui/macro';
import { useCallback, useMemo } from 'react';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { UserRoles } from '../../../enums/Roles';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { TableColumn } from '../Column';
import { BooleanColumn, DescriptionColumn } from '../ColumnRenderers';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowDeleteAction, RowEditAction } from '../RowActions';

export default function PartTestTemplateTable({ params }: { params: any }) {
  const table = useTable('part-test-template');
  const user = useUserState();

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'test_name',
        title: t`Test Name`,
        switchable: false,
        sortable: true
      },
      DescriptionColumn({
        switchable: false
      }),
      BooleanColumn({
        accessor: 'required',
        title: t`Required`
      }),
      BooleanColumn({
        accessor: 'requires_value',
        title: t`Requires Value`
      }),
      BooleanColumn({
        accessor: 'requires_attachment',
        title: t`Requires Attachment`
      })
    ];
  }, [params]);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'required',
        label: t`Required`,
        description: t`Show required tests`
      },
      {
        name: 'requires_value',
        label: t`Requires Value`,
        description: t`Show tests that require a value`
      },
      {
        name: 'requires_attachment',
        label: t`Requires Attachment`,
        description: t`Show tests that require an attachment`
      }
    ];
  }, []);

  const rowActions = useCallback(
    (record: any) => {
      let can_edit = user.hasChangeRole(UserRoles.part);
      let can_delete = user.hasDeleteRole(UserRoles.part);

      return [
        RowEditAction({
          hidden: !can_edit,
          onClick: () => {
            // TODO
          }
        }),
        RowDeleteAction({
          hidden: !can_delete,
          onClick: () => {
            // TODO
          }
        })
      ];
    },
    [user]
  );

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.part_test_template_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        params: {
          ...params
        },
        customFilters: tableFilters,
        rowActions: rowActions
      }}
    />
  );
}
