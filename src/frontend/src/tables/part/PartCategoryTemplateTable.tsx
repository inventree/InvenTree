import { t } from '@lingui/core/macro';
import { Group, Text } from '@mantine/core';
import { useCallback, useMemo, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import { AddItemButton } from '../../components/buttons/AddItemButton';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import { InvenTreeTable } from '../InvenTreeTable';
import { type RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

export default function PartCategoryTemplateTable() {
  const table = useTable('part-category-parameter-templates');
  const user = useUserState();

  const formFields: ApiFormFieldSet = useMemo(() => {
    return {
      category: {},
      parameter_template: {},
      default_value: {}
    };
  }, []);

  const [selectedTemplate, setSelectedTemplate] = useState<number>(0);

  const newTemplate = useCreateApiFormModal({
    url: ApiEndpoints.category_parameter_list,
    title: t`Add Category Parameter`,
    fields: useMemo(() => ({ ...formFields }), [formFields]),
    table: table
  });

  const editTemplate = useEditApiFormModal({
    url: ApiEndpoints.category_parameter_list,
    pk: selectedTemplate,
    title: t`Edit Category Parameter`,
    fields: useMemo(() => ({ ...formFields }), [formFields]),
    table: table
  });

  const deleteTemplate = useDeleteApiFormModal({
    url: ApiEndpoints.category_parameter_list,
    pk: selectedTemplate,
    title: t`Delete Category Parameter`,
    table: table
  });

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
          if (!record?.default_value) {
            return '-';
          }

          let units = '';

          if (record?.parameter_template_detail?.units) {
            units = `[${record.parameter_template_detail.units}]`;
          }

          return (
            <Group justify='space-between' grow>
              <Text>{record.default_value}</Text>
              {units && <Text size='xs'>{units}</Text>}
            </Group>
          );
        }
      }
    ];
  }, []);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
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
        key='add'
        tooltip={t`Add Category Parameter`}
        onClick={() => newTemplate.open()}
        hidden={!user.hasAddRole(UserRoles.part)}
      />
    ];
  }, [user]);

  return (
    <>
      {newTemplate.modal}
      {editTemplate.modal}
      {deleteTemplate.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.category_parameter_list)}
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
