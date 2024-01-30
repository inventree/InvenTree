import { t } from '@lingui/macro';
import { Text } from '@mantine/core';
import { useCallback, useMemo, useState } from 'react';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { UserRoles } from '../../../enums/Roles';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../../hooks/UseForm';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { AddItemButton } from '../../buttons/AddItemButton';
import { ApiFormFieldSet } from '../../forms/fields/ApiFormField';
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
        accessor: 'part_detail.IPN',
        title: t`IPN`,
        sortable: false,
        switchable: true
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

  const partParameterFields: ApiFormFieldSet = {
    part: {},
    template: {},
    data: {}
  };

  const newParameter = useCreateApiFormModal({
    url: ApiPaths.part_parameter_list,
    title: t`New Part Parameter`,
    fields: partParameterFields,
    initialData: {
      part: partId
    },
    onFormSuccess: table.refreshTable
  });

  const [selectedParameter, setSelectedParameter] = useState<
    number | undefined
  >(undefined);

  const editParameter = useEditApiFormModal({
    url: ApiPaths.part_parameter_list,
    pk: selectedParameter,
    title: t`Edit Part Parameter`,
    fields: partParameterFields,
    onFormSuccess: table.refreshTable
  });

  const deleteParameter = useDeleteApiFormModal({
    url: ApiPaths.part_parameter_list,
    pk: selectedParameter,
    title: t`Delete Part Parameter`,
    onFormSuccess: table.refreshTable
  });

  // Callback for row actions
  const rowActions = useCallback(
    (record: any) => {
      // Actions not allowed for "variant" rows
      if (String(partId) != String(record.part)) {
        return [];
      }

      return [
        RowEditAction({
          tooltip: t`Edit Part Parameter`,
          hidden: !user.hasChangeRole(UserRoles.part),
          onClick: () => {
            setSelectedParameter(record.pk);
            editParameter.open();
          }
        }),
        RowDeleteAction({
          tooltip: t`Delete Part Parameter`,
          hidden: !user.hasDeleteRole(UserRoles.part),
          onClick: () => {
            setSelectedParameter(record.pk);
            deleteParameter.open();
          }
        })
      ];
    },
    [partId, user]
  );

  // Custom table actions
  const tableActions = useMemo(() => {
    let actions = [];

    // TODO: Hide if user does not have permission to edit parts
    actions.push(
      <AddItemButton
        tooltip={t`Add parameter`}
        onClick={() => newParameter.open()}
      />
    );

    return actions;
  }, []);

  return (
    <>
      {newParameter.modal}
      {editParameter.modal}
      {deleteParameter.modal}
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
    </>
  );
}
