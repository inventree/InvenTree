import { t } from '@lingui/core/macro';
import { Group, Tooltip } from '@mantine/core';
import { IconBell } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import { type RowAction, RowEditAction } from '@lib/components/RowActions';
import { YesNoButton } from '@lib/components/YesNoButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { ActionDropdown } from '../../components/items/ActionDropdown';
import { ApiIcon } from '../../components/items/ApiIcon';
import { partCategoryFields } from '../../forms/PartForms';
import { InvenTreeIcon } from '../../functions/icons';
import {
  useBulkEditApiFormModal,
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import { DescriptionColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

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
        sortable: true
      },
      {
        accessor: 'structural',
        sortable: true,
        defaultVisible: false,
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

  const setParent = useBulkEditApiFormModal({
    url: ApiEndpoints.category_list,
    items: table.selectedIds,
    title: t`Set Parent Category`,
    fields: {
      parent: {}
    },
    onFormSuccess: table.refreshTable
  });

  const tableActions = useMemo(() => {
    const can_add = user.hasAddRole(UserRoles.part_category);
    const can_edit = user.hasChangeRole(UserRoles.part_category);

    return [
      <ActionDropdown
        tooltip={t`Category Actions`}
        icon={<InvenTreeIcon icon='category' />}
        disabled={!table.hasSelectedRecords}
        actions={[
          {
            name: t`Set Parent`,
            icon: <InvenTreeIcon icon='category' />,
            tooltip: t`Set parent category for the selected items`,
            hidden: !can_edit,
            disabled: !table.hasSelectedRecords,
            onClick: () => {
              setParent.open();
            }
          }
        ]}
      />,
      <AddItemButton
        key='add-part-category'
        tooltip={t`Add Part Category`}
        onClick={() => newCategory.open()}
        hidden={!can_add}
      />
    ];
  }, [user, table.hasSelectedRecords]);

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
      {setParent.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.category_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          enableDownload: true,
          enableSelection: true,
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
