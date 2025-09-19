import { t } from '@lingui/core/macro';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import {
  type RowAction,
  RowDeleteAction,
  RowDuplicateAction,
  RowEditAction
} from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import type { TableColumn } from '@lib/types/Tables';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import { BooleanColumn, DescriptionColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

export default function PartParameterTemplateTable() {
  const table = useTable('part-parameter-templates');

  const user = useUserState();

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'checkbox',
        label: t`Checkbox`,
        description: t`Show checkbox templates`
      },
      {
        name: 'has_choices',
        label: t`Has choices`,
        description: t`Show templates with choices`
      },
      {
        name: 'has_units',
        label: t`Has Units`,
        description: t`Show templates with units`
      }
    ];
  }, []);

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        sortable: true,
        switchable: false
      },
      {
        accessor: 'parts',
        sortable: true,
        switchable: true
      },
      {
        accessor: 'units',
        sortable: true
      },
      DescriptionColumn({}),
      BooleanColumn({
        accessor: 'checkbox'
      }),
      {
        accessor: 'choices'
      }
    ];
  }, []);

  const partParameterTemplateFields: ApiFormFieldSet = useMemo(() => {
    return {
      name: {},
      description: {},
      units: {},
      choices: {},
      checkbox: {},
      selectionlist: {}
    };
  }, []);

  const newTemplate = useCreateApiFormModal({
    url: ApiEndpoints.part_parameter_template_list,
    title: t`Add Parameter Template`,
    table: table,
    fields: useMemo(
      () => ({ ...partParameterTemplateFields }),
      [partParameterTemplateFields]
    )
  });

  const [selectedTemplate, setSelectedTemplate] = useState<any | undefined>(
    undefined
  );

  const duplicateTemplate = useCreateApiFormModal({
    url: ApiEndpoints.part_parameter_template_list,
    title: t`Duplicate Parameter Template`,
    table: table,
    fields: useMemo(
      () => ({ ...partParameterTemplateFields }),
      [partParameterTemplateFields]
    ),
    initialData: selectedTemplate
  });

  const editTemplate = useEditApiFormModal({
    url: ApiEndpoints.part_parameter_template_list,
    pk: selectedTemplate?.pk,
    title: t`Edit Parameter Template`,
    table: table,
    fields: useMemo(
      () => ({ ...partParameterTemplateFields }),
      [partParameterTemplateFields]
    )
  });

  const deleteTemplate = useDeleteApiFormModal({
    url: ApiEndpoints.part_parameter_template_list,
    pk: selectedTemplate?.pk,
    title: t`Delete Parameter Template`,
    table: table
  });

  // Callback for row actions
  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.part),
          onClick: () => {
            setSelectedTemplate(record);
            editTemplate.open();
          }
        }),
        RowDuplicateAction({
          hidden: !user.hasAddRole(UserRoles.part),
          onClick: () => {
            setSelectedTemplate(record);
            duplicateTemplate.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.part),
          onClick: () => {
            setSelectedTemplate(record);
            deleteTemplate.open();
          }
        })
      ];
    },
    [user]
  );

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add'
        tooltip={t`Add Parameter Template`}
        onClick={() => newTemplate.open()}
        hidden={!user.hasAddRole(UserRoles.part)}
      />
    ];
  }, [user]);

  return (
    <>
      {newTemplate.modal}
      {editTemplate.modal}
      {duplicateTemplate.modal}
      {deleteTemplate.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.part_parameter_template_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          rowActions: rowActions,
          tableFilters: tableFilters,
          tableActions: tableActions,
          enableDownload: true
        }}
      />
    </>
  );
}
