import { t } from '@lingui/macro';
import { Drawer, Group, LoadingOverlay, Stack, Text } from '@mantine/core';
import { ReactTree } from '@naisutech/react-tree';
import { IconSitemap } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';

import { api } from '../../App';
import { ApiPaths } from '../../enums/ApiEndpoints';
import { apiUrl } from '../../states/ApiState';
import { StylishText } from '../items/StylishText';

export function PartCategoryTree({
  opened,
  onClose,
  selectedCategory
}: {
  opened: boolean;
  onClose: () => void;
  selectedCategory?: number | null;
}) {
  const navigate = useNavigate();

  const treeQuery = useQuery({
    enabled: opened,
    queryKey: ['part_category_tree', opened],
    queryFn: async () =>
      api
        .get(apiUrl(ApiPaths.category_tree), {})
        .then((response) =>
          response.data.map((category: any) => {
            return {
              id: category.pk,
              label: category.name,
              parentId: category.parent
            };
          })
        )
        .catch((error) => {
          console.error('Error fetching part categpry tree:', error);
          return error;
        }),
    refetchOnMount: true
  });

  function renderNode({ node }: { node: any }) {
    return (
      <Group
        position="apart"
        key={node.id}
        noWrap={true}
        onClick={() => {
          onClose();
          navigate(`/part/category/${node.id}`);
        }}
      >
        <Text>{node.label}</Text>
      </Group>
    );
  }

  return (
    <Drawer
      opened={opened}
      size="md"
      position="left"
      onClose={onClose}
      withCloseButton={true}
      styles={{
        header: {
          width: '100%'
        },
        title: {
          width: '100%'
        }
      }}
      title={
        <Group position="left" p="ms" spacing="md" noWrap={true}>
          <IconSitemap />
          <StylishText size="lg">{t`Part Categories`}</StylishText>
        </Group>
      }
    >
      <Stack spacing="xs">
        <LoadingOverlay visible={treeQuery.isFetching} />
        <ReactTree
          nodes={treeQuery.data ?? []}
          RenderNode={renderNode}
          defaultSelectedNodes={selectedCategory ? [selectedCategory] : []}
          showEmptyItems={false}
        />
      </Stack>
    </Drawer>
  );
}
