import { t } from '@lingui/macro';
import {
  Drawer,
  Group,
  LoadingOverlay,
  Stack,
  Text,
  useMantineColorScheme
} from '@mantine/core';
import { ReactTree, ThemeSettings } from '@naisutech/react-tree';
import {
  IconChevronDown,
  IconChevronRight,
  IconSitemap
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { apiUrl } from '../../states/ApiState';
import { theme, vars } from '../../theme';
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
              parentId: category.parent,
              children: category.subcategories
            };
          })
        )
        .catch((error) => {
          console.error('Error fetching part category tree:', error);
          return [];
        }),
    refetchOnMount: true
  });

  function renderNode({ node }: { node: any }) {
    return (
      <Group
        justify="space-between"
        key={node.id}
        wrap="nowrap"
        onClick={() => {
          onClose();
          navigate(`/part/category/${node.id}`);
        }}
      >
        <Text>{node.label}</Text>
      </Group>
    );
  }

  function renderIcon({ node, open }: { node: any; open?: boolean }) {
    if (node.children == 0) {
      return undefined;
    }

    return open ? <IconChevronDown /> : <IconChevronRight />;
  }

  const { colorScheme } = useMantineColorScheme();

  const themes: ThemeSettings = useMemo(() => {
    const currentTheme =
      colorScheme === 'dark'
        ? vars.colors.defaultColor
        : vars.colors.primaryColors;

    return {
      dark: {
        text: {
          fontFamily: vars.fontFamily,
          //fontSize: vars.fontSizes.md,
          color: vars.colors.text
        },
        nodes: {
          height: '2.5rem',
          folder: {
            selectedBgColor: currentTheme[4],
            hoverBgColor: currentTheme[6]
          },
          leaf: {
            selectedBgColor: currentTheme[4],
            hoverBgColor: currentTheme[6]
          },
          icons: {
            folderColor: currentTheme[3],
            leafColor: currentTheme[3]
          }
        }
      },
      light: {
        text: {
          fontFamily: vars.fontFamily,
          //fontSize: vars.fontSizes.md,
          color: vars.colors.text
        },
        nodes: {
          height: '2.5rem',
          folder: {
            selectedBgColor: currentTheme[4],
            hoverBgColor: currentTheme[2]
          },
          leaf: {
            selectedBgColor: currentTheme[4],
            hoverBgColor: currentTheme[2]
          },
          icons: {
            folderColor: currentTheme[8],
            leafColor: currentTheme[6]
          }
        }
      }
    };
  }, [theme]);

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
        <Group justify="left" p="ms" gap="md" wrap="nowrap">
          <IconSitemap />
          <StylishText size="lg">{t`Part Categories`}</StylishText>
        </Group>
      }
    >
      <Stack gap="xs">
        <LoadingOverlay visible={treeQuery.isFetching} />
        <ReactTree
          nodes={treeQuery.data ?? []}
          RenderNode={renderNode}
          RenderIcon={renderIcon}
          defaultSelectedNodes={selectedCategory ? [selectedCategory] : []}
          showEmptyItems={false}
          theme={colorScheme}
          themes={themes}
        />
      </Stack>
    </Drawer>
  );
}
