import { t } from '@lingui/macro';
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
        title: t`Test Name`,
        switchable: false,
        sortable: true
      },
      DescriptionColumn({
        switchable: false
      }),
      BooleanColumn({
        accessor: 'required',
        title: t`Required`
      }),
      BooleanColumn({
        accessor: 'requires_value',
        title: t`Requires Value`
      }),
      BooleanColumn({
        accessor: 'requires_attachment',
        title: t`Requires Attachment`
      })
    ];
  }, []);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'required',
        label: t`Required`,
        description: t`Show required tests`
      },
      {
        name: 'requires_value',
        label: t`Requires Value`,
        description: t`Show tests that require a value`
      },
      {
        name: 'requires_attachment',
        label: t`Requires Attachment`,
        description: t`Show tests that require an attachment`
      }
    ];
  }, []);

  const partTestTemplateFields: ApiFormFieldSet = {
    part: {
      hidden: true
    },
    test_name: {},
    description: {},
    required: {},
    requires_value: {},
    requires_attachment: {}
  };

  const newTestTemplate = useCreateApiFormModal({
    url: ApiPaths.part_test_template_list,
    title: t`Add Test Template`,
    fields: partTestTemplateFields,
    initialData: {
      part: partId
    },
    onFormSuccess: table.refreshTable
  });

  const [selectedTest, setSelectedTest] = useState<number | undefined>(
    undefined
  );

  const editTestTemplate = useEditApiFormModal({
    url: ApiPaths.part_test_template_list,
    pk: selectedTest,
    title: t`Edit Test Template`,
    fields: partTestTemplateFields,
    onFormSuccess: table.refreshTable
  });

  const deleteTestTemplate = useDeleteApiFormModal({
    url: ApiPaths.part_test_template_list,
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
        url={apiUrl(ApiPaths.part_test_template_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            part: partId
          },
          tableFilters: tableFilters,
          tableActions: tableActions,
          rowActions: rowActions
        }}
      />
    </>
  );
}
