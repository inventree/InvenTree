import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import { Alert, Badge, Text } from '@mantine/core';
import { type ReactNode, useCallback, useMemo, useState } from 'react';

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
import useTable from '@lib/hooks/UseTable';
import type { TableFilter } from '@lib/types/Filters';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import type { TableColumn } from '@lib/types/Tables';
import {
  BooleanColumn,
  DescriptionColumn
} from '../../components/tables/ColumnRenderers';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import { TableHoverCard } from '../../components/tables/TableHoverCard';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useUserState } from '../../states/UserState';

export function TestTemplateTable() {
  const table = useTable('part-test-template');
  const user = useUserState();

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'test_name',
        switchable: false,
        sortable: true,
        render: (record: any) => {
          const extra: ReactNode[] = [];

          return (
            <TableHoverCard
              value={<Text>{record.test_name}</Text>}
              title={t`Template Details`}
              extra={extra}
            />
          );
        }
      },
      {
        accessor: 'results',
        switchable: true,
        sortable: true,
        title: t`Results`,
        render: (record: any) => {
          return record.results || <Badge color='blue'>{t`No Results`}</Badge>;
        }
      },
      DescriptionColumn({
        switchable: false
      }),
      {
        accessor: 'choices',
        sortable: false,
        switchable: true
      },
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
        name: 'requires_value',
        label: t`Requires Value`,
        description: t`Show tests that require a value`
      },
      {
        name: 'requires_attachment',
        label: t`Requires Attachment`,
        description: t`Show tests that require an attachment`
      },
      {
        name: 'has_results',
        label: t`Has Results`,
        description: t`Show tests which have recorded results`
      }
    ];
  }, []);

  const partTestTemplateFields: ApiFormFieldSet = useMemo(() => {
    return {
      test_name: {},
      description: {},
      requires_value: {},
      requires_attachment: {},
      choices: {}
    };
  }, []);

  const newTestTemplate = useCreateApiFormModal({
    url: ApiEndpoints.part_test_template_list,
    title: t`Add Test Template`,
    fields: useMemo(
      () => ({ ...partTestTemplateFields }),
      [partTestTemplateFields]
    ),
    initialData: {},
    table: table
  });

  const [selectedTest, setSelectedTest] = useState<number>(-1);

  // Initial data for a duplicated test template
  const [duplicateData, setDuplicateData] = useState<any>({});

  const duplicateTestTemplate = useCreateApiFormModal({
    url: ApiEndpoints.part_test_template_list,
    title: t`Duplicate Test Template`,
    preFormWarning: t`Test template names must be unique - enter a new name for the duplicated template`,
    fields: useMemo(
      () => ({ ...partTestTemplateFields }),
      [partTestTemplateFields]
    ),
    initialData: duplicateData,
    table: table
  });

  const editTestTemplate = useEditApiFormModal({
    url: ApiEndpoints.part_test_template_list,
    pk: selectedTest,
    title: t`Edit Test Template`,
    preFormWarning: t`Changes to this test template will affect all parts which use this template (including locked parts)`,
    table: table,
    fields: useMemo(
      () => ({ ...partTestTemplateFields }),
      [partTestTemplateFields]
    )
  });

  const deleteTestTemplate = useDeleteApiFormModal({
    url: ApiEndpoints.part_test_template_list,
    pk: selectedTest,
    title: t`Delete Test Template`,
    preFormContent: (
      <Alert color='red' title={t`This action cannot be reversed`}>
        <Text>
          <Trans>
            Any tests results associated with this template will be deleted
          </Trans>
        </Text>
      </Alert>
    ),
    table: table
  });

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      const can_add = user.hasAddRole(UserRoles.part);
      const can_edit = user.hasChangeRole(UserRoles.part);
      const can_delete = user.hasDeleteRole(UserRoles.part);

      return [
        RowEditAction({
          hidden: !can_edit,
          onClick: () => {
            setSelectedTest(record.pk);
            editTestTemplate.open();
          }
        }),
        RowDuplicateAction({
          hidden: !can_add,
          onClick: () => {
            setDuplicateData({
              test_name: record.test_name,
              description: record.description,
              requires_value: record.requires_value,
              requires_attachment: record.requires_attachment,
              choices: record.choices
            });
            duplicateTestTemplate.open();
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
    const can_add = user.hasAddRole(UserRoles.part);

    return [
      <AddItemButton
        key='add-test-template'
        tooltip={t`Add Test Template`}
        onClick={() => newTestTemplate.open()}
        hidden={!can_add}
      />
    ];
  }, [user]);

  return (
    <>
      {newTestTemplate.modal}
      {editTestTemplate.modal}
      {duplicateTestTemplate.modal}
      {deleteTestTemplate.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.part_test_template_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          tableFilters: tableFilters,
          tableActions: tableActions,
          enableDownload: true,
          rowActions: rowActions
        }}
      />
    </>
  );
}
