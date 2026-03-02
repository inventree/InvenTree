import {
  AddItemButton,
  ApiEndpoints,
  type ApiFormFieldSet,
  ModelType,
  type RowAction,
  RowDeleteAction,
  RowEditAction,
  RowViewAction,
  apiUrl
} from '@lib/index';
import { t } from '@lingui/core/macro';
import { useCallback, useMemo, useState } from 'react';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';

import type { TableColumn } from '@lib/types/Tables';
import { Group } from '@mantine/core';
import { useNavigate } from 'react-router-dom';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import {
  CategoryColumn,
  DescriptionColumn,
  PartColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { TableHoverCard } from '../TableHoverCard';

export function PartTestTable({
  partId,
  categoryId
}: Readonly<{
  partId?: number;
  categoryId?: number;
}>) {
  const user = useUserState();
  const navigate = useNavigate();
  const table = useTable('part-test');
  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      PartColumn({
        accessor: 'part_detail',
        switchable: true
      }),
      CategoryColumn({
        accessor: 'category_detail',
        switchable: true
      }),
      {
        accessor: 'template_detail.test_name',
        title: t`Template`,
        switchable: false,
        render: (record: any) => {
          const extra = [];

          if (record.part && partId && record.part != partId) {
            extra.push(t`Test defined for a higher level part`);
          }

          if (record.category && categoryId && record.category != categoryId) {
            extra.push(t`Test defined for a higher level category`);
          }

          return (
            <Group gap='xs' wrap='nowrap' justify='space-between'>
              {record.template_detail.test_name}
              {extra && (
                <TableHoverCard
                  value=''
                  position='bottom-end'
                  icon='info'
                  title={t`Details`}
                  extra={extra}
                />
              )}
            </Group>
          );
        }
      },
      DescriptionColumn({
        accessor: 'template_detail.description',
        switchable: true
      })
    ];
  }, [partId, categoryId]);

  const partTestFields: ApiFormFieldSet = useMemo(() => {
    return {
      part: {},
      category: {},
      template: {}
    };
  }, []);

  const [selectedTestId, setSelectedTestId] = useState<number | undefined>(
    undefined
  );

  const newTest = useCreateApiFormModal({
    url: ApiEndpoints.part_test_list,
    title: t`Add Test`,
    fields: useMemo(() => ({ ...partTestFields }), [partTestFields]),
    initialData: {
      part: partId,
      category: categoryId
    },
    focus: 'template',
    table: table
  });

  const editTest = useEditApiFormModal({
    url: ApiEndpoints.part_test_list,
    pk: selectedTestId,
    title: t`Edit Test`,
    fields: useMemo(() => ({ ...partTestFields }), [partTestFields]),
    focus: 'template',
    table: table
  });

  const deleteTest = useDeleteApiFormModal({
    url: ApiEndpoints.part_test_list,
    pk: selectedTestId,
    title: t`Delete Test`,
    table: table
  });

  // TODO: Table filters

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-test'
        tooltip={t`Add Test`}
        onClick={() => {
          newTest.open();
        }}
      />
    ];
  }, []);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      // This test is defined for a different part
      if (partId && record.part != partId) {
        return [
          RowViewAction({
            title: t`View Part`,
            modelType: ModelType.part,
            modelId: record.part,
            navigate: navigate
          })
        ];
      }

      // This test is defined for a different category
      if (categoryId && record.category != categoryId) {
        return [
          RowViewAction({
            title: t`View Category`,
            modelType: ModelType.partcategory,
            modelId: record.category,
            navigate: navigate
          })
        ];
      }

      return [
        RowEditAction({
          hidden: !user.hasChangePermission(ModelType.parttest),
          onClick: () => {
            setSelectedTestId(record.pk);
            editTest.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeletePermission(ModelType.parttest),
          onClick: () => {
            setSelectedTestId(record.pk);
            deleteTest.open();
          }
        })
      ];
    },
    [partId, categoryId, navigate, user]
  );

  return (
    <>
      {newTest.modal}
      {editTest.modal}
      {deleteTest.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.part_test_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            part: partId,
            category: categoryId
          },
          rowActions: rowActions,
          tableActions: tableActions
        }}
      />
    </>
  );
}
