import { t } from '@lingui/core/macro';
import { Alert, Group, Stack, Text } from '@mantine/core';
import { IconInfoCircle, IconLock } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AddItemButton } from '@lib/components/AddItemButton';
import {
  type RowAction,
  RowDeleteAction,
  RowEditAction
} from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import type { TableFilter } from '@lib/types/Filters';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import type { TableColumn } from '@lib/types/Tables';
import { AppRowViewAction } from '../../components/tables/AppRowActions';
import {
  BooleanColumn,
  DescriptionColumn,
  PartColumn,
  PathColumn
} from '../../components/tables/ColumnRenderers';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import { TableHoverCard } from '../../components/tables/TableHoverCard';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useUserState } from '../../states/UserState';

/**
 * Table for displaying the tests which apply to a Part or PartCategory.
 *
 * - Tests may be linked directly to the part (or category)
 * - Tests may be inherited from a parent part, the part category, or a parent category
 * - Only tests which are linked directly can be edited from this table
 */
export function PartTestTable({
  partId,
  categoryId,
  partLocked
}: Readonly<{
  partId?: number;
  categoryId?: number;
  partLocked?: boolean;
}>) {
  const user = useUserState();
  const navigate = useNavigate();
  const table = useTable(categoryId ? 'category-test' : 'part-test');

  // Is this test linked directly to the part (or category) being viewed?
  const isDirect = useCallback(
    (record: any): boolean => {
      if (partId) {
        return record.part == partId;
      }

      if (categoryId) {
        return record.category == categoryId;
      }

      return true;
    },
    [partId, categoryId]
  );

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'template_detail.test_name',
        title: t`Test`,
        switchable: false,
        render: (record: any) => {
          const extra: string[] = [];

          if (!isDirect(record)) {
            if (record.part) {
              extra.push(t`Test defined for a higher level part`);
            } else if (record.category) {
              extra.push(
                partId
                  ? t`Test defined for the part category`
                  : t`Test defined for a parent category`
              );
            }
          }

          return (
            <Group gap='xs' wrap='nowrap' justify='space-between'>
              {record.template_detail?.test_name}
              {extra.length > 0 && (
                <TableHoverCard
                  value=''
                  position='bottom-end'
                  icon='info'
                  title={t`Inherited Test`}
                  extra={extra}
                />
              )}
            </Group>
          );
        }
      },
      PartColumn({
        accessor: 'part_detail',
        title: t`Part`,
        switchable: true,
        hidden: !!categoryId
      }),
      PathColumn({
        accessor: 'category_detail',
        title: t`Category`,
        switchable: true
      }),
      DescriptionColumn({
        accessor: 'template_detail.description',
        switchable: true
      }),
      BooleanColumn({
        accessor: 'enabled',
        title: t`Enabled`,
        switchable: true,
        sortable: true
      }),
      BooleanColumn({
        accessor: 'required',
        title: t`Required`,
        switchable: true,
        sortable: true
      }),
      BooleanColumn({
        accessor: 'template_detail.requires_value',
        title: t`Requires Value`,
        switchable: true,
        sortable: false,
        defaultVisible: false
      }),
      BooleanColumn({
        accessor: 'template_detail.requires_attachment',
        title: t`Requires Attachment`,
        switchable: true,
        sortable: false,
        defaultVisible: false
      })
    ];
  }, [partId, categoryId, isDirect]);

  const partTestFields: ApiFormFieldSet = useMemo(() => {
    return {
      part: {
        hidden: !!categoryId
      },
      category: {
        hidden: !!partId
      },
      template: {},
      enabled: {},
      required: {}
    };
  }, [partId, categoryId]);

  const [selectedTestId, setSelectedTestId] = useState<number | undefined>(
    undefined
  );

  const newTest = useCreateApiFormModal({
    url: ApiEndpoints.part_test_list,
    title: t`Add Test`,
    fields: partTestFields,
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
    fields: partTestFields,
    focus: 'template',
    table: table
  });

  const deleteTest = useDeleteApiFormModal({
    url: ApiEndpoints.part_test_list,
    pk: selectedTestId,
    title: t`Delete Test`,
    table: table
  });

  // Table filters
  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'enabled',
        label: t`Enabled`,
        description: t`Show enabled tests`
      },
      {
        name: 'required',
        label: t`Required`,
        description: t`Show required tests`
      },
      {
        name: 'include_inherited',
        label: t`Include Inherited`,
        description: t`Show tests inherited from parent parts or categories`
      }
    ];
  }, []);

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-test'
        tooltip={t`Add Test`}
        hidden={partLocked || !user.hasAddPermission(ModelType.parttest)}
        onClick={() => {
          newTest.open();
        }}
      />
    ];
  }, [user, partLocked]);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      // Inherited tests can only be edited against the part or category they are defined for
      if (!isDirect(record)) {
        if (record.part) {
          return [
            AppRowViewAction({
              title: t`View Part`,
              modelType: ModelType.part,
              modelId: record.part,
              navigate: navigate
            })
          ];
        }

        return [
          AppRowViewAction({
            title: t`View Category`,
            modelType: ModelType.partcategory,
            modelId: record.category,
            navigate: navigate
          })
        ];
      }

      return [
        RowEditAction({
          hidden: partLocked || !user.hasChangePermission(ModelType.parttest),
          onClick: () => {
            setSelectedTestId(record.pk);
            editTest.open();
          }
        }),
        RowDeleteAction({
          hidden: partLocked || !user.hasDeletePermission(ModelType.parttest),
          onClick: () => {
            setSelectedTestId(record.pk);
            deleteTest.open();
          }
        })
      ];
    },
    [isDirect, partLocked, navigate, user]
  );

  return (
    <>
      {newTest.modal}
      {editTest.modal}
      {deleteTest.modal}
      <Stack gap='xs'>
        {categoryId && (
          <Alert
            title={t`Category Tests`}
            color='blue'
            icon={<IconInfoCircle />}
            p='xs'
          >
            <Text>{t`Tests defined for this category apply to all parts in this category, and in any subcategories.`}</Text>
          </Alert>
        )}
        {partLocked && (
          <Alert
            title={t`Part is Locked`}
            color='orange'
            icon={<IconLock />}
            p='xs'
          >
            <Text>{t`Part tests cannot be edited, as the part is locked`}</Text>
          </Alert>
        )}
        <InvenTreeTable
          url={apiUrl(ApiEndpoints.part_test_list)}
          tableState={table}
          columns={tableColumns}
          props={{
            params: {
              for_part: partId,
              for_category: categoryId
            },
            rowActions: rowActions,
            tableFilters: tableFilters,
            tableActions: tableActions
          }}
        />
      </Stack>
    </>
  );
}
