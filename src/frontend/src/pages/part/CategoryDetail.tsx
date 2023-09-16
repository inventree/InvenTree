import { t } from '@lingui/macro';
import { Stack, Text } from '@mantine/core';
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

/**
 * Detail view for a single PartCategory instance.
 *
 * Note: If no category ID is supplied, this acts as the top-level part category page
 */
export default function CategoryDetail({}: {}) {
  const { id } = useParams();

  const [category, setCategory] = useState<any>({});

  useEffect(() => {
    setCategory({});
  }, [id]);

  const categoryQuery = useQuery({
    enabled: id != null && id != undefined,
    queryKey: ['category', id],
    queryFn: async () => {
      return api
        .get(`/part/category/${id}/`)
        .then((response) => {
          setCategory(response.data);
          return response.data;
        })
        .catch((error) => {
          console.error('Error fetching category data:', error);
        });
    }
  });

  const categoryPanels: PanelType[] = useMemo(
    () => [
      {
        name: 'parts',
        label: t`Parts`,
        icon: <IconCategory size="18" />,
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
        label: t`Subcategories`,
        icon: <IconSitemap size="18" />,
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
        icon: <IconListDetails size="18" />,
        content: <PlaceholderPanel />
      }
    ],
    [category, id]
  );

  return (
    <Stack spacing="xs">
      <PageDetail
        title={t`Part Category`}
        detail={<Text>{category.name ?? 'Top level'}</Text>}
        breadcrumbs={
          id
            ? [
                { name: t`Parts`, url: '/part' },
                { name: '...', url: '' },
                {
                  name: category.name ?? t`Top level`,
                  url: `/part/category/${category.pk}`
                }
              ]
            : []
        }
      />
      <PanelGroup panels={categoryPanels} />
    </Stack>
  );
}
