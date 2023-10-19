import { t } from '@lingui/macro';
import { LoadingOverlay, Stack, Text } from '@mantine/core';
import {
  IconCategory,
  IconListDetails,
  IconSitemap
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { api } from '../../App';
import { PlaceholderPanel } from '../../components/items/Placeholder';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { PartCategoryTable } from '../../components/tables/part/PartCategoryTable';
import { PartListTable } from '../../components/tables/part/PartTable';
import { useInstance } from '../../hooks/UseInstance';
import { ApiPaths } from '../../states/ApiState';

/**
 * Detail view for a single PartCategory instance.
 *
 * Note: If no category ID is supplied, this acts as the top-level part category page
 */
export default function CategoryDetail({}: {}) {
  const { id } = useParams();

  const {
    instance: category,
    refreshInstance,
    instanceQuery
  } = useInstance({
    endpoint: ApiPaths.category_list,
    pk: id,
    params: {
      path_detail: true
    }
  });

  const categoryPanels: PanelType[] = useMemo(
    () => [
      {
        name: 'parts',
        label: t`Parts`,
        icon: <IconCategory />,
        content: (
          <PartListTable
            props={{
              params: {
                category: category.pk ?? null
              }
            }}
          />
        )
      },
      {
        name: 'subcategories',
        label: t`Part Categories`,
        icon: <IconSitemap />,
        content: (
          <PartCategoryTable
            params={{
              parent: category.pk ?? null
            }}
          />
        )
      },
      {
        name: 'parameters',
        label: t`Parameters`,
        icon: <IconListDetails />,
        content: <PlaceholderPanel />
      }
    ],
    [category, id]
  );

  const breadcrumbs = useMemo(
    () => [
      { name: t`Parts`, url: '/part' },
      ...(category.path ?? []).map((c: any) => ({
        name: c.name,
        url: `/part/category/${c.pk}`
      }))
    ],
    [category]
  );

  return (
    <Stack spacing="xs">
      <LoadingOverlay visible={instanceQuery.isFetching} />
      <PageDetail
        title={t`Part Category`}
        detail={<Text>{category.name ?? 'Top level'}</Text>}
        breadcrumbs={breadcrumbs}
      />
      <PanelGroup pageKey="partcategory" panels={categoryPanels} />
    </Stack>
  );
}
