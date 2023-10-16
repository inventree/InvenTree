import { t } from '@lingui/macro';
import { Text } from '@mantine/core';
import { useCallback, useMemo } from 'react';

import { openDeleteApiForm, openEditApiForm } from '../../../functions/forms';
import { useTableRefresh } from '../../../hooks/TableRefresh';
import { ApiPaths, apiUrl } from '../../../states/ApiState';
import { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * Construct a table listing parameters for a given part
 */
export function PartParameterTable({ partId }: { partId: any }) {
  const { tableKey, refreshTable } = useTableRefresh('part-parameters');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Parameter`,
        switchable: false,
        sortable: true,
        render: (record) => record.template_detail?.name
      },
      {
        accessor: 'description',
        title: t`Description`,
        sortable: false,
        switchable: true,
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
            // TODO: Render boolean chip
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
        switchable: true,
        sortable: true,
        render: (record) => record.template_detail?.units
      }
    ];
  }, []);

  // Callback for row actions
  // TODO: Adjust based on user permissions
  const rowActions = useCallback((record: any) => {
    let actions = [];

    actions.push({
      title: t`Edit`,
      onClick: () => {
        openEditApiForm({
          name: 'edit-part-parameter',
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
          onFormSuccess: refreshTable
        });
      }
    });

    actions.push({
      title: t`Delete`,
      color: 'red',
      onClick: () => {
        openDeleteApiForm({
          name: 'delete-part-parameter',
          url: ApiPaths.part_parameter_list,
          pk: record.pk,
          title: t`Delete Part Parameter`,
          successMessage: t`Part parameter deleted`,
          onFormSuccess: refreshTable,
          preFormContent: (
            <Text>{t`Are you sure you want to remove this parameter?`}</Text>
          )
        });
      }
    });

    return actions;
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.part_parameter_list)}
      tableKey={tableKey}
      columns={tableColumns}
      props={{
        rowActions: rowActions,
        params: {
          part: partId,
          template_detail: true
        }
      }}
    />
  );
}
