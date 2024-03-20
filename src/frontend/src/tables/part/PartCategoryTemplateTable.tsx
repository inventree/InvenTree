import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import { useCallback, useMemo } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowDeleteAction, RowEditAction } from '../RowActions';

export default function PartCategoryTemplateTable({}: {}) {
  const table = useTable('part-category-parameter-templates');
  const user = useUserState();

  const tableFilters: TableFilter[] = useMemo(() => {
    // TODO
    return [];
  }, []);

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'category_detail.name',
        title: t`Category`,
        sortable: true,
        switchable: false
      },
      {
        accessor: 'category_detail.pathstring'
      },
      {
        accessor: 'parameter_template_detail.name',
        title: t`Parameter Template`,
        sortable: true,
        switchable: false
      },
      {
        accessor: 'default_value',
        sortable: true,
        switchable: false,
        render: (record: any) => {
          let units = '';

          if (record?.parameter_template_detail?.units) {
            units = t`[${record.parameter_template_detail.units}]`;
          }

          return (
            <Group position="apart" grow>
              <Text>{record.default_value}</Text>
              {units && <Text size="xs">{units}</Text>}
            </Group>
          );
        }
      }
    ];
  }, []);

  const rowActions = useCallback(
    (record: any) => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.part),
          onClick: () => {
            // TODO
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.part),
          onClick: () => {
            // TODO
          }
        })
      ];
    },
    [user]
  );

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        tooltip={t`Add Category Parameter`}
        onClick={() => {
          // TODO
        }}
        hidden={!user.hasAddRole(UserRoles.part)}
      />
    ];
  }, [user]);

  return (
    <>
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.category_parameter_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          rowActions: rowActions,
          tableFilters: tableFilters,
          tableActions: tableActions
        }}
      />
    </>
  );
}
