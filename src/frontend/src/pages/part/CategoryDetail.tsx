import { t } from '@lingui/core/macro';
import { LoadingOverlay, Stack } from '@mantine/core';
import {
  IconCategory,
  IconInfoCircle,
  IconListCheck,
  IconListDetails,
  IconPackages,
  IconSitemap,
  IconTable
} from '@tabler/icons-react';
import { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { getDetailUrl } from '@lib/functions/Navigation';
import type { StockOperationProps } from '@lib/types/Forms';
import type { PanelType } from '@lib/types/Panel';
import { useLocalStorage } from '@mantine/hooks';
import AdminButton from '../../components/buttons/AdminButton';
import StarredToggleButton from '../../components/buttons/StarredToggleButton';
import {
  DeleteItemAction,
  EditItemAction,
  OptionsActionDropdown
} from '../../components/items/ActionDropdown';
import { ApiIcon } from '../../components/items/ApiIcon';
import InstanceDetail from '../../components/nav/InstanceDetail';
import NavigationTree from '../../components/nav/NavigationTree';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup } from '../../components/panels/PanelGroup';
import ParametersPanel from '../../components/panels/ParametersPanel';
import SegmentedControlPanel from '../../components/panels/SegmentedControlPanel';
import { partCategoryFields } from '../../forms/PartForms';
import {
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { useStockAdjustActions } from '../../hooks/UseStockAdjustActions';
import { useUserSettingsState } from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';
import ParametricPartTable from '../../tables/part/ParametricPartTable';
import { PartCategoryTable } from '../../tables/part/PartCategoryTable';
import PartCategoryTemplateTable from '../../tables/part/PartCategoryTemplateTable';
import { PartListTable } from '../../tables/part/PartTable';
import { StockItemTable } from '../../tables/stock/StockItemTable';
import { PartCategoryDetailsPanel } from './PartCategoryDetailsPanel';

/**
 * Detail view for a single PartCategory instance.
 *
 * Note: If no category ID is supplied, this acts as the top-level part category page
 */
export default function CategoryDetail() {
  const { id: _id } = useParams();
  const id = useMemo(
    () => (!Number.isNaN(Number.parseInt(_id || '')) ? _id : undefined),
    [_id]
  );

  const navigate = useNavigate();
  const user = useUserState();
  const settings = useUserSettingsState();

  const [treeOpen, setTreeOpen] = useState(false);

  const {
    instance: category,
    refreshInstance,
    instanceQuery
  } = useInstance({
    endpoint: ApiEndpoints.category_list,
    hasPrimaryKey: true,
    pk: id,
    params: {
      path_detail: true
    }
  });

  const stockOperationProps: StockOperationProps = useMemo(() => {
    return {
      refresh: refreshInstance,
      filters: {
        category: category.pk,
        in_stock: true
      }
    };
  }, [category]);

  const stockAdjustActions = useStockAdjustActions({
    formProps: stockOperationProps,
    enabled: true,
    add: false,
    remove: false,
    changeStatus: false,
    changeBatch: false,
    delete: false,
    merge: false,
    assign: false
  });

  const editCategory = useEditApiFormModal({
    url: ApiEndpoints.category_list,
    pk: id,
    title: t`Edit Part Category`,
    fields: partCategoryFields({}),
    onFormSuccess: refreshInstance
  });

  const deleteOptions = useMemo(() => {
    return [
      {
        value: 'false',
        display_name: t`Move items to parent category`
      },
      {
        value: 'true',
        display_name: t`Delete items`
      }
    ];
  }, []);

  const deleteCategory = useDeleteApiFormModal({
    url: ApiEndpoints.category_list,
    pk: id,
    title: t`Delete Part Category`,
    fields: {
      delete_parts: {
        label: t`Parts Action`,
        description: t`Action for parts in this category`,
        choices: deleteOptions,
        required: true,
        field_type: 'choice'
      },
      delete_child_categories: {
        label: t`Child Categories Action`,
        description: t`Action for child categories in this category`,
        choices: deleteOptions,
        required: true,
        field_type: 'choice'
      }
    },
    onFormSuccess: () => {
      if (category.parent) {
        navigate(getDetailUrl(ModelType.partcategory, category.parent));
      } else {
        navigate('/part/');
      }
    }
  });

  const categoryActions = useMemo(() => {
    return [
      <AdminButton
        key='admin'
        model={ModelType.partcategory}
        id={category.pk}
      />,
      <StarredToggleButton
        key='starred_change'
        instance={category}
        model={ModelType.partcategory}
        successFunction={() => {
          refreshInstance();
        }}
      />,
      stockAdjustActions.dropdown,
      <OptionsActionDropdown
        key='category-actions'
        tooltip={t`Category Actions`}
        actions={[
          EditItemAction({
            hidden: !id || !user.hasChangeRole(UserRoles.part_category),
            tooltip: t`Edit Part Category`,
            onClick: () => editCategory.open()
          }),
          DeleteItemAction({
            hidden: !id || !user.hasDeleteRole(UserRoles.part_category),
            tooltip: t`Delete Part Category`,
            onClick: () => deleteCategory.open()
          })
        ]}
      />
    ];
  }, [id, user, category.pk, category.starred, stockAdjustActions.dropdown]);

  const [partsView, setPartsView] = useLocalStorage<string>({
    key: 'category-parts-view',
    defaultValue: 'table'
  });

  const panels: PanelType[] = useMemo(
    () => [
      {
        name: 'details',
        label: t`Category Details`,
        icon: <IconInfoCircle />,
        content: <PartCategoryDetailsPanel instance={category} />,
        hidden: !id || !category?.pk
      },
      {
        name: 'subcategories',
        label: id ? t`Subcategories` : t`Part Categories`,
        icon: <IconSitemap />,
        content: <PartCategoryTable parentId={id} />
      },
      SegmentedControlPanel({
        name: 'parts',
        label: t`Parts`,
        icon: <IconCategory />,
        selection: partsView,
        onChange: setPartsView,
        options: [
          {
            value: 'table',
            label: t`Table View`,
            icon: <IconTable />,
            content: (
              <PartListTable
                props={{
                  params: {
                    category: id
                  }
                }}
              />
            )
          },
          {
            value: 'parametric',
            label: t`Parametric View`,
            icon: <IconListDetails />,
            content: <ParametricPartTable categoryId={id} />
          }
        ]
      }),
      {
        name: 'stockitem',
        label: t`Stock Items`,
        icon: <IconPackages />,
        hidden: !id,
        content: (
          <StockItemTable
            params={{
              category: id
            }}
            allowAdd={false}
            tableName='category-stockitems'
          />
        )
      },
      ParametersPanel({
        model_type: ModelType.partcategory,
        model_id: category?.pk,
        hidden: !id || !category.pk
      }),
      {
        name: 'category_parameters',
        label: t`Parameter Templates`,
        icon: <IconListCheck />,
        hidden: !id || !category.pk,
        content: <PartCategoryTemplateTable categoryId={category?.pk} />
      }
    ],
    [category, id, partsView]
  );

  const breadcrumbs = useMemo(
    () => [
      { name: t`Parts`, url: '/part' },
      ...(category.path ?? []).map((c: any) => ({
        name: c.name,
        url: getDetailUrl(ModelType.partcategory, c.pk),
        icon: c.icon ? <ApiIcon name={c.icon} /> : undefined
      }))
    ],
    [category]
  );

  const defaultPanel = useMemo(() => {
    if (
      settings.isSet('DISPLAY_ITEMS_FINAL_LEVEL', true) &&
      category.pk &&
      category.subcategories === 0
    ) {
      return 'parts';
    }
    return undefined;
  }, [settings, category]);

  return (
    <>
      {editCategory.modal}
      {deleteCategory.modal}
      {stockAdjustActions.modals.map((modal) => modal.modal)}
      <InstanceDetail
        query={instanceQuery}
        requiredRole={UserRoles.part_category}
      >
        <Stack gap='xs'>
          <LoadingOverlay visible={instanceQuery.isFetching} />
          <NavigationTree
            modelType={ModelType.partcategory}
            title={t`Part Categories`}
            endpoint={ApiEndpoints.category_tree}
            childIdentifier='subcategories'
            opened={treeOpen}
            onClose={() => {
              setTreeOpen(false);
            }}
            selectedId={category?.pk}
          />
          <PageDetail
            title={(category?.name ?? id) ? t`Part Category` : t`Parts`}
            subtitle={category?.description}
            icon={category?.icon && <ApiIcon name={category?.icon} />}
            breadcrumbs={breadcrumbs}
            breadcrumbAction={() => {
              setTreeOpen(true);
            }}
            actions={categoryActions}
            editAction={editCategory.open}
            editEnabled={
              !!category?.pk && user.hasChangePermission(ModelType.partcategory)
            }
          />
          <PanelGroup
            pageKey='partcategory'
            panels={panels}
            model={ModelType.partcategory}
            instance={category}
            reloadInstance={refreshInstance}
            id={category.pk ?? null}
            defaultPanel={defaultPanel}
          />
        </Stack>
      </InstanceDetail>
    </>
  );
}
