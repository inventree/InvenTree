import { t } from '@lingui/macro';
import { Text } from '@mantine/core';
import { useCallback, useMemo } from 'react';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { UserRoles } from '../../../enums/Roles';
import {
  openCreateApiForm,
  openDeleteApiForm,
  openEditApiForm
} from '../../../functions/forms';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { AddItemButton } from '../../buttons/AddItemButton';
import { YesNoButton } from '../../items/YesNoButton';
import { TableColumn } from '../Column';
import { PartColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowDeleteAction, RowEditAction } from '../RowActions';

/**
 * Construct a table listing parameters for a given part
 */
export function PartParameterTable({ partId }: { partId: any }) {
  const table = useTable('part-parameters');

  const user = useUserState();

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'part',
        title: t`Part`,

        sortable: true,
        render: (record: any) => PartColumn(record?.part_detail)
      },
      {
        accessor: 'name',
        title: t`Parameter`,
        switchable: false,
        sortable: true,
        render: (record) => {
          let variant = String(partId) != String(record.part);

          return <Text italic={variant}>{record.template_detail?.name}</Text>;
        }
      },
      {
        accessor: 'description',
        title: t`Description`,
        sortable: false,

        render: (record) => record.template_detail?.description
      },
      {
        accessor: 'data',
        title: t`Value`,
        switchable: false,
        sortable: true,
        render: (record) => {
          let template = record.template_detail;

          if (template?.checkbox) {
            return <YesNoButton value={record.data} />;
          }

          if (record.data_numeric) {
            // TODO: Numeric data
          }

          // TODO: Units

          return record.data;
        }
      },
      {
        accessor: 'units',
        title: t`Units`,

        sortable: true,
        render: (record) => record.template_detail?.units
      }
    ];
  }, [partId]);

  // Callback for row actions
  const rowActions = useCallback(
    (record: any) => {
      // Actions not allowed for "variant" rows
      if (String(partId) != String(record.part)) {
        return [];
      }

      let actions = [];

      actions.push(
        RowEditAction({
          tooltip: t`Edit Part Parameter`,
          hidden: !user.hasChangeRole(UserRoles.part),
          onClick: () => {
            openEditApiForm({
              url: ApiPaths.part_parameter_list,
              pk: record.pk,
              title: t`Edit Part Parameter`,
              fields: {
                part: {
                  hidden: true
                },
                template: {},
                data: {}
              },
              successMessage: t`Part parameter updated`,
              onFormSuccess: table.refreshTable
            });
          }
        })
      );

      actions.push(
        RowDeleteAction({
          tooltip: t`Delete Part Parameter`,
          hidden: !user.hasDeleteRole(UserRoles.part),
          onClick: () => {
            openDeleteApiForm({
              url: ApiPaths.part_parameter_list,
              pk: record.pk,
              title: t`Delete Part Parameter`,
              successMessage: t`Part parameter deleted`,
              onFormSuccess: table.refreshTable,
              preFormWarning: t`Are you sure you want to remove this parameter?`
            });
          }
        })
      );

      return actions;
    },
    [partId, user]
  );

  const addParameter = useCallback(() => {
    if (!partId) {
      return;
    }

    openCreateApiForm({
      url: ApiPaths.part_parameter_list,
      title: t`Add Part Parameter`,
      fields: {
        part: {
          hidden: true,
          value: partId
        },
        template: {},
        data: {}
      },
      successMessage: t`Part parameter added`,
      onFormSuccess: table.refreshTable
    });
  }, [partId]);

  // Custom table actions
  const tableActions = useMemo(() => {
    let actions = [];

    // TODO: Hide if user does not have permission to edit parts
    actions.push(
      <AddItemButton tooltip={t`Add parameter`} onClick={addParameter} />
    );

    return actions;
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.part_parameter_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        rowActions: rowActions,
        tableActions: tableActions,
        tableFilters: [
          {
            name: 'include_variants',
            label: t`Include Variants`,
            type: 'boolean'
          }
        ],
        params: {
          part: partId,
          template_detail: true,
          part_detail: true
        }
      }}
    />
  );
}
