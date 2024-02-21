import { t } from '@lingui/macro';
import { Text } from '@mantine/core';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { ApiFormFieldSet } from '../../components/forms/fields/ApiFormField';
import { YesNoButton } from '../../components/items/YesNoButton';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { DescriptionColumn, PartColumn } from '../ColumnRenderers';
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
        sortable: true,
        render: (record: any) => PartColumn(record?.part_detail)
      },
      {
        accessor: 'part_detail.IPN',
        sortable: false,
        switchable: true
      },
      {
        accessor: 'template_detail.name',
        switchable: false,
        sortable: true,
        ordering: 'name',
        render: (record) => {
          let variant = String(partId) != String(record.part);

          return <Text italic={variant}>{record.template_detail?.name}</Text>;
        }
      },
      DescriptionColumn({
        accessor: 'template_detail.description'
      }),
      {
        accessor: 'data',
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
        accessor: 'template_detail.units',
        ordering: 'units',
        sortable: true
      }
    ];
  }, [partId]);

  const partParameterFields: ApiFormFieldSet = useMemo(() => {
    return {
      part: {},
      template: {},
      data: {}
    };
  }, []);

  const newParameter = useCreateApiFormModal({
    url: ApiEndpoints.part_parameter_list,
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
    url: ApiEndpoints.part_parameter_list,
    pk: selectedParameter,
    title: t`Edit Part Parameter`,
    fields: partParameterFields,
    onFormSuccess: table.refreshTable
  });

  const deleteParameter = useDeleteApiFormModal({
    url: ApiEndpoints.part_parameter_list,
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
    return [
      <AddItemButton
        hidden={!user.hasAddRole(UserRoles.part)}
        tooltip={t`Add parameter`}
        onClick={() => newParameter.open()}
      />
    ];
  }, [user]);

  return (
    <>
      {newParameter.modal}
      {editParameter.modal}
      {deleteParameter.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.part_parameter_list)}
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
