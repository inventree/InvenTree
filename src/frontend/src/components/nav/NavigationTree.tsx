import {
  ActionIcon,
  Anchor,
  Divider,
  Drawer,
  Group,
  LoadingOverlay,
  type RenderTreeNodePayload,
  Space,
  Stack,
  Tree,
  type TreeNodeData,
  useTree
} from '@mantine/core';
import {
  IconChevronDown,
  IconChevronRight,
  IconSitemap
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { useApi } from '../../contexts/ApiContext';
import type { ApiEndpoints } from '../../enums/ApiEndpoints';
import type { ModelType } from '../../enums/ModelType';
import { navigateToLink } from '../../functions/navigation';
import { getDetailUrl } from '../../functions/urls';
import { apiUrl } from '../../states/ApiState';
import { ApiIcon } from '../items/ApiIcon';
import { StylishText } from '../items/StylishText';

/*
 * A generic navigation tree component.
 */
export default function NavigationTree({
  title,
  opened,
  onClose,
  selectedId,
  modelType,
  endpoint
}: Readonly<{
  title: string;
  opened: boolean;
  onClose: () => void;
  selectedId?: number | null;
  modelType: ModelType;
  endpoint: ApiEndpoints;
}>) {
  const api = useApi();
  const navigate = useNavigate();
  const treeState = useTree();

  // Data query to fetch the tree data from server
  const query = useQuery({
    enabled: opened,
    queryKey: [modelType, opened],
    queryFn: async () =>
      api
        .get(apiUrl(endpoint), {
          data: {
            ordering: 'level'
          }
        })
        .then((response) => response.data ?? [])
        .catch((error) => {
          console.error(`Error fetching ${modelType} tree`);
          return [];
        })
  });

  const follow = useCallback(
    (node: TreeNodeData, event?: any) => {
      const url = getDetailUrl(modelType, node.value);
      if (event?.shiftKey || event?.ctrlKey) {
        navigateToLink(url, navigate, event);
      } else {
        onClose();
        navigate(url);
      }
    },
    [modelType, navigate]
  );

  // Map returned query to a "tree" structure
  const data: TreeNodeData[] = useMemo(() => {
    /*
     * Reconstruct the navigation tree from the provided data.
     * It is required (and assumed) that the data is first sorted by level.
     */

    const nodes: Record<number, any> = {};
    const tree: TreeNodeData[] = [];

    if (!query?.data?.length) {
      return [];
    }

    for (let ii = 0; ii < query.data.length; ii++) {
      const node = {
        ...query.data[ii],
        children: [],
        label: (
          <Group gap='xs'>
            <ApiIcon name={query.data[ii].icon} />
            {query.data[ii].name}
          </Group>
        ),
        value: query.data[ii].pk.toString(),
        selected: query.data[ii].pk === selectedId
      };

      const pk: number = node.pk;
      const parent: number | null = node.parent;

      if (!parent) {
        // This is a top level node
        tree.push(node);
      } else {
        // This is *not* a top level node, so the parent *must* already exist
        nodes[parent]?.children.push(node);
      }

      // Finally, add this node
      nodes[pk] = node;

      if (pk === selectedId) {
        // Expand all parents
        let parent = nodes[node.parent];
        while (parent) {
          parent.expanded = true;
          parent = nodes[parent.parent];
        }
      }
    }

    return tree;
  }, [selectedId, query.data]);

  const renderNode = useCallback(
    (payload: RenderTreeNodePayload) => {
      return (
        <Group
          justify='left'
          key={payload.node.value}
          wrap='nowrap'
          onClick={() => {
            if (payload.hasChildren) {
              treeState.toggleExpanded(payload.node.value);
            }
          }}
        >
          <Space w={5 * payload.level} />
          <ActionIcon
            size='sm'
            variant='transparent'
            aria-label={`nav-tree-toggle-${payload.node.value}}`}
          >
            {payload.hasChildren ? (
              payload.expanded ? (
                <IconChevronDown />
              ) : (
                <IconChevronRight />
              )
            ) : null}
          </ActionIcon>
          <Anchor
            onClick={(event: any) => follow(payload.node, event)}
            aria-label={`nav-tree-item-${payload.node.value}`}
          >
            {payload.node.label}
          </Anchor>
        </Group>
      );
    },
    [treeState]
  );

  return (
    <Drawer
      opened={opened}
      size='md'
      position='left'
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
        <Group justify='left' p='ms' gap='md' wrap='nowrap'>
          <IconSitemap />
          <StylishText size='lg'>{title}</StylishText>
        </Group>
      }
    >
      <Stack gap='xs'>
        <Divider />
        <LoadingOverlay visible={query.isFetching || query.isLoading} />
        <Tree data={data} tree={treeState} renderNode={renderNode} />
      </Stack>
    </Drawer>
  );
}
