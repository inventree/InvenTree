import { t } from '@lingui/macro';
import {
  Drawer,
  Group,
  LoadingOverlay,
  Stack,
  Text,
  useMantineTheme
} from '@mantine/core';
import { ReactTree, ThemeSettings } from '@naisutech/react-tree';
import { IconSitemap } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
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
        .get(apiUrl(ApiEndpoints.category_tree), {})
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
          console.error('Error fetching part category tree:', error);
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

  const mantineTheme = useMantineTheme();
  const currentTheme =
    mantineTheme.colorScheme === 'dark'
      ? mantineTheme.colorScheme
      : mantineTheme.primaryColor;

  const themes: ThemeSettings = {
    dark: {
      text: {
        ...mantineTheme.fn.fontStyles()
      },
      nodes: {
        height: '2.5rem',
        folder: {
          selectedBgColor: mantineTheme.colors[currentTheme][4],
          hoverBgColor: mantineTheme.colors[currentTheme][6]
        },
        leaf: {
          selectedBgColor: mantineTheme.colors[currentTheme][4],
          hoverBgColor: mantineTheme.colors[currentTheme][6]
        },
        icons: {
          folderColor: mantineTheme.colors[currentTheme][3],
          leafColor: mantineTheme.colors[currentTheme][3]
        }
      }
    },
    light: {
      text: {
        ...mantineTheme.fn.fontStyles()
      },
      nodes: {
        height: '2.5rem',
        folder: {
          selectedBgColor: mantineTheme.colors[currentTheme][4],
          hoverBgColor: mantineTheme.colors[currentTheme][2]
        },
        leaf: {
          bgColor: 'initial',
          selectedBgColor: mantineTheme.colors[currentTheme][4],
          hoverBgColor: mantineTheme.colors[currentTheme][2]
        },
        icons: {
          folderColor: mantineTheme.colors[currentTheme][8],
          leafColor: mantineTheme.colors[currentTheme][6]
        }
      }
    }
  };

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
          theme={mantineTheme.colorScheme}
          themes={themes}
        />
      </Stack>
    </Drawer>
  );
}
