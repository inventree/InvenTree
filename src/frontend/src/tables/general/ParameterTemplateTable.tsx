import {
  AddItemButton,
  ApiEndpoints,
  type ApiFormFieldSet,
  RowDeleteAction,
  RowDuplicateAction,
  RowEditAction,
  UserRoles,
  apiUrl
} from '@lib/index';
import type { TableFilter } from '@lib/types/Filters';
import type { RowAction, TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { useCallback, useMemo, useState } from 'react';
import { useFilters } from '../../hooks/UseFilter';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import { BooleanColumn, DescriptionColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * Render a table of ParameterTemplate objects
 */
export default function ParameterTemplateTable() {
  const table = useTable('parameter-templates');
  const user = useUserState();

  const parameterTemplateFields: ApiFormFieldSet = useMemo(() => {
    return {
      name: {},
      description: {},
      units: {},
      model_type: {},
      choices: {},
      checkbox: {},
      selectionlist: {},
      enabled: {}
    };
  }, []);

  const newTemplate = useCreateApiFormModal({
    url: ApiEndpoints.parameter_template_list,
    title: t`Add Parameter Template`,
    table: table,
    fields: useMemo(
      () => ({
        ...parameterTemplateFields
      }),
      [parameterTemplateFields]
    )
  });

  const [selectedTemplate, setSelectedTemplate] = useState<any | undefined>(
    undefined
  );

  const duplicateTemplate = useCreateApiFormModal({
    url: ApiEndpoints.parameter_template_list,
    title: t`Duplicate Parameter Template`,
    table: table,
    fields: useMemo(
      () => ({
        ...parameterTemplateFields
      }),
      [parameterTemplateFields]
    ),
    initialData: selectedTemplate
  });

  const deleteTemplate = useDeleteApiFormModal({
    url: ApiEndpoints.parameter_template_list,
    pk: selectedTemplate?.pk,
    title: t`Delete Parameter Template`,
    table: table
  });

  const editTemplate = useEditApiFormModal({
    url: ApiEndpoints.parameter_template_list,
    pk: selectedTemplate?.pk,
    title: t`Edit Parameter Template`,
    table: table,
    fields: useMemo(
      () => ({
        ...parameterTemplateFields
      }),
      [parameterTemplateFields]
    )
  });

  // Callback for row actions
  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          onClick: () => {
            setSelectedTemplate(record);
            editTemplate.open();
          }
        }),
        RowDuplicateAction({
          onClick: () => {
            setSelectedTemplate(record);
            duplicateTemplate.open();
          }
        }),
        RowDeleteAction({
          onClick: () => {
            setSelectedTemplate(record);
            deleteTemplate.open();
          }
        })
      ];
    },
    [user]
  );

  const modelTypeFilters = useFilters({
    url: apiUrl(ApiEndpoints.parameter_template_list),
    method: 'OPTIONS',
    accessor: 'data.actions.POST.model_type.choices',
    transform: (item: any) => {
      return {
        value: item.value,
        label: item.display_name
      };
    }
  });

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
      },
      {
        name: 'enabled',
        label: t`Enabled`,
        description: t`Show enabled templates`
      },
      {
        name: 'model_type',
        label: t`Model Type`,
        description: t`Filter by model type`,
        choices: modelTypeFilters.choices
      }
    ];
  }, [modelTypeFilters.choices]);

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        sortable: true,
        switchable: false
      },
      DescriptionColumn({}),
      {
        accessor: 'units',
        sortable: true
      },
      {
        accessor: 'model_type'
      },
      BooleanColumn({
        accessor: 'checkbox'
      }),
      {
        accessor: 'choices'
      },
      BooleanColumn({
        accessor: 'enabled',
        title: t`Enabled`
      })
    ];
  }, []);

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
        url={apiUrl(ApiEndpoints.parameter_template_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          rowActions: rowActions,
          tableActions: tableActions,
          tableFilters: tableFilters,
          enableDownload: true
        }}
      />
    </>
  );
}
