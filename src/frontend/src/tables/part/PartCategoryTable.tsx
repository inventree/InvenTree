import { t } from '@lingui/macro';
import { Group, Tooltip } from '@mantine/core';
import { IconBell } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { YesNoButton } from '../../components/buttons/YesNoButton';
import { ApiIcon } from '../../components/items/ApiIcon';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { partCategoryFields } from '../../forms/PartForms';
import {
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import { DescriptionColumn } from '../ColumnRenderers';
import type { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { type RowAction, RowEditAction } from '../RowActions';

/**
 * PartCategoryTable - Displays a table of part categories
 */
export function PartCategoryTable({ parentId }: Readonly<{ parentId?: any }>) {
  const table = useTable('partcategory');
  const user = useUserState();

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        sortable: true,
        switchable: false,
        render: (record: any) => (
          <Group gap='xs' wrap='nowrap' justify='space-between'>
            <Group gap='xs' wrap='nowrap'>
              {record.icon && <ApiIcon name={record.icon} />}
              {record.name}
            </Group>
            <Group gap='xs' justify='flex-end' wrap='nowrap'>
              {record.starred && (
                <Tooltip
                  label={t`You are subscribed to notifications for this category`}
                >
                  <IconBell color='green' size={16} />
                </Tooltip>
              )}
            </Group>
          </Group>
        )
      },
      DescriptionColumn({}),
      {
        accessor: 'pathstring',
        sortable: false
      },
      {
        accessor: 'structural',
        sortable: true,
        render: (record: any) => {
          return <YesNoButton value={record.structural} />;
        }
      },
      {
        accessor: 'part_count',
        sortable: true
      }
    ];
  }, []);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'cascade',
        label: t`Include Subcategories`,
        description: t`Include subcategories in results`
      },
      {
        name: 'structural',
        label: t`Structural`,
        description: t`Show structural categories`
      },
      {
        name: 'starred',
        label: t`Subscribed`,
        description: t`Show categories to which the user is subscribed`
      }
    ];
  }, []);

  const newCategoryFields = partCategoryFields({ create: true });

  const newCategory = useCreateApiFormModal({
    url: ApiEndpoints.category_list,
    title: t`New Part Category`,
    fields: newCategoryFields,
    focus: 'name',
    initialData: {
      parent: parentId
    },
    follow: true,
    modelType: ModelType.partcategory,
    table: table
  });

  const [selectedCategory, setSelectedCategory] = useState<number>(-1);

  const editCategoryFields = partCategoryFields({ create: false });

  const editCategory = useEditApiFormModal({
    url: ApiEndpoints.category_list,
    pk: selectedCategory,
    title: t`Edit Part Category`,
    fields: editCategoryFields,
    onFormSuccess: (record: any) => table.updateRecord(record)
  });

  const tableActions = useMemo(() => {
    const can_add = user.hasAddRole(UserRoles.part_category);

    return [
      <AddItemButton
        key='add-part-category'
        tooltip={t`Add Part Category`}
        onClick={() => newCategory.open()}
        hidden={!can_add}
      />
    ];
  }, [user]);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      const can_edit = user.hasChangeRole(UserRoles.part_category);

      return [
        RowEditAction({
          hidden: !can_edit,
          onClick: () => {
            setSelectedCategory(record.pk);
            editCategory.open();
          }
        })
      ];
    },
    [user]
  );

  return (
    <>
      {newCategory.modal}
      {editCategory.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.category_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          enableDownload: true,
          params: {
            parent: parentId,
            top_level: parentId === undefined ? true : undefined
          },
          tableFilters: tableFilters,
          tableActions: tableActions,
          rowActions: rowActions,
          modelType: ModelType.partcategory
        }}
      />
    </>
  );
}
