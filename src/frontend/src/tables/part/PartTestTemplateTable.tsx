import { t } from '@lingui/macro';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { ApiFormFieldSet } from '../../components/forms/fields/ApiFormField';
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
import { BooleanColumn, DescriptionColumn } from '../ColumnRenderers';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowDeleteAction, RowEditAction } from '../RowActions';

export default function PartTestTemplateTable({ partId }: { partId: number }) {
  const table = useTable('part-test-template');
  const user = useUserState();

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'test_name',
        switchable: false,
        sortable: true
      },
      DescriptionColumn({
        switchable: false
      }),
      BooleanColumn({
        accessor: 'required'
      }),
      BooleanColumn({
        accessor: 'requires_value'
      }),
      BooleanColumn({
        accessor: 'requires_attachment'
      })
    ];
  }, []);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'required',
        description: t`Show required tests`
      },
      {
        name: 'requires_value',
        description: t`Show tests that require a value`
      },
      {
        name: 'requires_attachment',
        description: t`Show tests that require an attachment`
      },
      {
        name: 'include_inherited',
        label: t`Include Inherited`,
        description: t`Show tests from inherited templates`
      }
    ];
  }, []);

  const partTestTemplateFields: ApiFormFieldSet = useMemo(() => {
    return {
      part: {
        hidden: true
      },
      test_name: {},
      description: {},
      required: {},
      requires_value: {},
      requires_attachment: {}
    };
  }, []);

  const newTestTemplate = useCreateApiFormModal({
    url: ApiEndpoints.part_test_template_list,
    title: t`Add Test Template`,
    fields: partTestTemplateFields,
    initialData: {
      part: partId
    },
    onFormSuccess: table.refreshTable
  });

  const [selectedTest, setSelectedTest] = useState<number>(-1);

  const editTestTemplate = useEditApiFormModal({
    url: ApiEndpoints.part_test_template_list,
    pk: selectedTest,
    title: t`Edit Test Template`,
    fields: partTestTemplateFields,
    onFormSuccess: table.refreshTable
  });

  const deleteTestTemplate = useDeleteApiFormModal({
    url: ApiEndpoints.part_test_template_list,
    pk: selectedTest,
    title: t`Delete Test Template`,
    onFormSuccess: table.refreshTable
  });

  const rowActions = useCallback(
    (record: any) => {
      let can_edit = user.hasChangeRole(UserRoles.part);
      let can_delete = user.hasDeleteRole(UserRoles.part);

      return [
        RowEditAction({
          hidden: !can_edit,
          onClick: () => {
            setSelectedTest(record.pk);
            editTestTemplate.open();
          }
        }),
        RowDeleteAction({
          hidden: !can_delete,
          onClick: () => {
            setSelectedTest(record.pk);
            deleteTestTemplate.open();
          }
        })
      ];
    },
    [user]
  );

  const tableActions = useMemo(() => {
    let can_add = user.hasAddRole(UserRoles.part);

    return [
      <AddItemButton
        tooltip={t`Add Test Template`}
        onClick={() => newTestTemplate.open()}
        disabled={!can_add}
      />
    ];
  }, [user]);

  return (
    <>
      {newTestTemplate.modal}
      {editTestTemplate.modal}
      {deleteTestTemplate.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.part_test_template_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            part: partId,
            part_detail: true
          },
          tableFilters: tableFilters,
          tableActions: tableActions,
          rowActions: rowActions
        }}
      />
    </>
  );
}
