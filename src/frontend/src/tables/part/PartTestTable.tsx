import {
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
        accessor: 'part_detail'
      }),
      CategoryColumn({
        accessor: 'category_detail'
      }),
      {
        accessor: 'template_detail.test_name',
        title: t`Template`,
        switchable: false
      },
      DescriptionColumn({
        accessor: 'template_detail.description'
      })
    ];
  }, []);

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
    table: table
  });

  const editTest = useEditApiFormModal({
    url: ApiEndpoints.part_test_list,
    pk: selectedTestId,
    title: t`Edit Test`,
    fields: useMemo(() => ({ ...partTestFields }), [partTestFields]),
    table: table
  });

  const deleteTest = useDeleteApiFormModal({
    url: ApiEndpoints.part_test_list,
    pk: selectedTestId,
    title: t`Delete Test`,
    table: table
  });

  // TODO: Table filters

  // TODO: Table actions

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
          rowActions: rowActions
        }}
      />
    </>
  );
}
