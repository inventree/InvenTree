import { t } from '@lingui/macro';
import { Group, LoadingOverlay, Skeleton, Stack, Text } from '@mantine/core';
import {
  IconCategory,
  IconInfoCircle,
  IconListDetails,
  IconSitemap
} from '@tabler/icons-react';
import { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import AdminButton from '../../components/buttons/AdminButton';
import { DetailsField, DetailsTable } from '../../components/details/Details';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import {
  DeleteItemAction,
  EditItemAction,
  OptionsActionDropdown
} from '../../components/items/ActionDropdown';
import { ApiIcon } from '../../components/items/ApiIcon';
import InstanceDetail from '../../components/nav/InstanceDetail';
import NavigationTree from '../../components/nav/NavigationTree';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { partCategoryFields } from '../../forms/PartForms';
import { getDetailUrl } from '../../functions/urls';
import {
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { useUserState } from '../../states/UserState';
import ParametricPartTable from '../../tables/part/ParametricPartTable';
import { PartCategoryTable } from '../../tables/part/PartCategoryTable';
import { PartListTable } from '../../tables/part/PartTable';

/**
 * Detail view for a single PartCategory instance.
 *
 * Note: If no category ID is supplied, this acts as the top-level part category page
 */
export default function CategoryDetail() {
  const { id: _id } = useParams();
  const id = useMemo(
    () => (!isNaN(parseInt(_id || '')) ? _id : undefined),
    [_id]
  );

  const navigate = useNavigate();
  const user = useUserState();

  const [treeOpen, setTreeOpen] = useState(false);

  const {
    instance: category,
    refreshInstance,
    instanceQuery,
    requestStatus
  } = useInstance({
    endpoint: ApiEndpoints.category_list,
    hasPrimaryKey: true,
    pk: id,
    params: {
      path_detail: true
    }
  });

  const detailsPanel = useMemo(() => {
    if (id && instanceQuery.isFetching) {
      return <Skeleton />;
    }

    let left: DetailsField[] = [
      {
        type: 'text',
        name: 'name',
        label: t`Name`,
        copy: true,
        value_formatter: () => (
          <Group gap="xs">
            {category.icon && <ApiIcon name={category.icon} />}
            {category.name}
          </Group>
        )
      },
      {
        type: 'text',
        name: 'pathstring',
        label: t`Path`,
        icon: 'sitemap',
        copy: true,
        hidden: !id
      },
      {
        type: 'text',
        name: 'description',
        label: t`Description`,
        copy: true
      },
      {
        type: 'link',
        name: 'parent',
        model_field: 'name',
        icon: 'location',
        label: t`Parent Category`,
        model: ModelType.partcategory,
        hidden: !category?.parent
      }
    ];

    let right: DetailsField[] = [
      {
        type: 'text',
        name: 'part_count',
        label: t`Parts`,
        icon: 'part',
        value_formatter: () => category?.part_count || '0'
      },
      {
        type: 'text',
        name: 'subcategories',
        label: t`Subcategories`,
        icon: 'sitemap',
        hidden: !category?.subcategories
      },
      {
        type: 'boolean',
        name: 'structural',
        label: t`Structural`,
        icon: 'sitemap'
      },
      {
        type: 'link',
        name: 'parent_default_location',
        label: t`Parent default location`,
        model: ModelType.stocklocation,
        hidden: !category.parent_default_location || category.default_location
      },
      {
        type: 'link',
        name: 'default_location',
        label: t`Default location`,
        model: ModelType.stocklocation,
        hidden: !category.default_location
      }
    ];

    return (
      <ItemDetailsGrid>
        {id && category?.pk ? (
          <DetailsTable item={category} fields={left} />
        ) : (
          <Text>{t`Top level part category`}</Text>
        )}
        {id && category?.pk && <DetailsTable item={category} fields={right} />}
      </ItemDetailsGrid>
    );
  }, [category, instanceQuery]);

  const editCategory = useEditApiFormModal({
    url: ApiEndpoints.category_list,
    pk: id,
    title: t`Edit Part Category`,
    fields: partCategoryFields(),
    onFormSuccess: refreshInstance
  });

  const deleteOptions = useMemo(() => {
    return [
      {
        value: 0,
        display_name: `Move items to parent category`
      },
      {
        value: 1,
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
        field_type: 'choice'
      },
      delete_child_categories: {
        label: t`Child Categories Action`,
        description: t`Action for child categories in this category`,
        choices: deleteOptions,
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
      <AdminButton model={ModelType.partcategory} pk={category.pk} />,
      <OptionsActionDropdown
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
  }, [id, user, category.pk]);

  const categoryPanels: PanelType[] = useMemo(
    () => [
      {
        name: 'details',
        label: t`Category Details`,
        icon: <IconInfoCircle />,
        content: detailsPanel
      },
      {
        name: 'parts',
        label: t`Parts`,
        icon: <IconCategory />,
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
        name: 'subcategories',
        label: t`Part Categories`,
        icon: <IconSitemap />,
        content: <PartCategoryTable parentId={id} />
      },
      {
        name: 'parameters',
        label: t`Part Parameters`,
        icon: <IconListDetails />,
        content: <ParametricPartTable categoryId={id} />
      }
    ],
    [category, id]
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

  return (
    <>
      {editCategory.modal}
      {deleteCategory.modal}
      <InstanceDetail
        status={requestStatus}
        loading={id ? instanceQuery.isFetching : false}
      >
        <Stack gap="xs">
          <LoadingOverlay visible={instanceQuery.isFetching} />
          <NavigationTree
            modelType={ModelType.partcategory}
            title={t`Part Categories`}
            endpoint={ApiEndpoints.category_tree}
            opened={treeOpen}
            onClose={() => {
              setTreeOpen(false);
            }}
            selectedId={category?.pk}
          />
          <PageDetail
            title={t`Part Category`}
            subtitle={category?.name}
            icon={category?.icon && <ApiIcon name={category?.icon} />}
            breadcrumbs={breadcrumbs}
            breadcrumbAction={() => {
              setTreeOpen(true);
            }}
            actions={categoryActions}
            editAction={editCategory.open}
            editEnabled={user.hasChangePermission(ModelType.partcategory)}
          />
          <PanelGroup pageKey="partcategory" panels={categoryPanels} />
        </Stack>
      </InstanceDetail>
    </>
  );
}
