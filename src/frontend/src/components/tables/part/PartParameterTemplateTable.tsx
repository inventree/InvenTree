import { t } from '@lingui/macro';
import { useCallback, useMemo, useState } from 'react';

import { ApiEndpoints } from '../../../enums/ApiEndpoints';
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
import { TableColumn } from '../Column';
import { DescriptionColumn } from '../ColumnRenderers';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowDeleteAction, RowEditAction } from '../RowActions';

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
        title: t`Name`,
        sortable: true,
        switchable: false
      },
      {
        accessor: 'units',
        title: t`Units`,
        sortable: true
      },
      DescriptionColumn({}),
      {
        accessor: 'checkbox',
        title: t`Checkbox`
      },
      {
        accessor: 'choices',
        title: t`Choices`
      }
    ];
  }, []);

  const partParameterTemplateFields: ApiFormFieldSet = {
    name: {},
    description: {},
    units: {},
    choices: {},
    checkbox: {}
  };

  const newTemplate = useCreateApiFormModal({
    url: ApiEndpoints.part_parameter_template_list,
    title: t`Add Parameter Template`,
    fields: partParameterTemplateFields,
    onFormSuccess: table.refreshTable
  });

  const [selectedTemplate, setSelectedTemplate] = useState<number | undefined>(
    undefined
  );

  const editTemplate = useEditApiFormModal({
    url: ApiEndpoints.part_parameter_template_list,
    pk: selectedTemplate,
    title: t`Edit Parameter Template`,
    fields: partParameterTemplateFields,
    onFormSuccess: table.refreshTable
  });

  const deleteTemplate = useDeleteApiFormModal({
    url: ApiEndpoints.part_parameter_template_list,
    pk: selectedTemplate,
    title: t`Delete Parameter Template`,
    onFormSuccess: table.refreshTable
  });

  // Callback for row actions
  const rowActions = useCallback(
    (record: any) => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.part),
          onClick: () => {
            setSelectedTemplate(record.pk);
            editTemplate.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.part),
          onClick: () => {
            setSelectedTemplate(record.pk);
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
        tooltip={t`Add parameter template`}
        onClick={() => newTemplate.open()}
        disabled={!user.hasAddRole(UserRoles.part)}
      />
    ];
  }, [user]);

  return (
    <>
      {newTemplate.modal}
      {editTemplate.modal}
      {deleteTemplate.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.part_parameter_template_list)}
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
