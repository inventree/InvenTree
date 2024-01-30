import { t } from '@lingui/macro';
import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { ApiEndpoints } from '../../../enums/ApiEndpoints';
import { ModelType } from '../../../enums/ModelType';
import { UserRoles } from '../../../enums/Roles';
import { partCategoryFields } from '../../../forms/PartForms';
import { openCreateApiForm, openEditApiForm } from '../../../functions/forms';
import { getDetailUrl } from '../../../functions/urls';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { AddItemButton } from '../../buttons/AddItemButton';
import { YesNoButton } from '../../items/YesNoButton';
import { TableColumn } from '../Column';
import { DescriptionColumn } from '../ColumnRenderers';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowEditAction } from '../RowActions';

/**
 * PartCategoryTable - Displays a table of part categories
 */
export function PartCategoryTable({ parentId }: { parentId?: any }) {
  const navigate = useNavigate();

  const table = useTable('partcategory');
  const user = useUserState();

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Name`,
        sortable: true,
        switchable: false
      },
      DescriptionColumn({}),
      {
        accessor: 'pathstring',
        title: t`Path`,
        sortable: false
      },
      {
        accessor: 'structural',
        title: t`Structural`,
        sortable: true,
        render: (record: any) => {
          return <YesNoButton value={record.structural} />;
        }
      },
      {
        accessor: 'part_count',
        title: t`Parts`,
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
      }
    ];
  }, []);

  const addCategory = useCallback(() => {
    let fields = partCategoryFields({});

    if (parentId) {
      fields['parent'].value = parentId;
    }

    openCreateApiForm({
      url: apiUrl(ApiEndpoints.category_list),
      title: t`Add Part Category`,
      fields: fields,
      onFormSuccess(data: any) {
        if (data.pk) {
          navigate(`/part/category/${data.pk}`);
        } else {
          table.refreshTable();
        }
      }
    });
  }, [parentId]);

  const tableActions = useMemo(() => {
    let can_add = user.hasAddRole(UserRoles.part_category);

    return [
      <AddItemButton
        tooltip={t`Add Part Category`}
        onClick={addCategory}
        disabled={!can_add}
      />
    ];
  }, [user]);

  const rowActions = useCallback(
    (record: any) => {
      let can_edit = user.hasChangeRole(UserRoles.part_category);

      return [
        RowEditAction({
          hidden: !can_edit,
          onClick: () => {
            openEditApiForm({
              url: ApiEndpoints.category_list,
              pk: record.pk,
              title: t`Edit Part Category`,
              fields: partCategoryFields({}),
              successMessage: t`Part category updated`,
              onFormSuccess: table.refreshTable
            });
          }
        })
      ];
    },
    [user]
  );

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.category_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        enableDownload: true,
        params: {
          parent: parentId ?? 'null'
        },
        tableFilters: tableFilters,
        tableActions: tableActions,
        rowActions: rowActions,
        onRowClick: (record, index, event) =>
          navigate(getDetailUrl(ModelType.partcategory, record.pk))
      }}
    />
  );
}
