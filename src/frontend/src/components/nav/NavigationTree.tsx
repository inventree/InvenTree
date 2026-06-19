import {
  ActionIcon,
  Alert,
  Anchor,
  Divider,
  Drawer,
  Group,
  LoadingOverlay,
  type RenderTreeNodePayload,
  Space,
  Stack,
  TextInput,
  Tree,
  type TreeNodeData,
  useTree
} from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import {
  IconChevronDown,
  IconChevronRight,
  IconExclamationCircle,
  IconSearch,
  IconSitemap,
  IconX
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { StylishText } from '@lib/components/StylishText';
import type { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import type { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { resolveItem } from '@lib/functions/Conversion';
import {
  eventModified,
  getDetailUrl,
  navigateToLink
} from '@lib/functions/Navigation';
import { t } from '@lingui/core/macro';
import { useApi } from '../../contexts/ApiContext';
import { ApiIcon } from '../items/ApiIcon';

/*
 * A generic navigation tree component.
 */
export default function NavigationTree({
  title,
  opened,
  onClose,
  selectedId,
  modelType,
  childIdentifier,
  endpoint
}: Readonly<{
  title: string;
  opened: boolean;
  onClose: () => void;
  selectedId?: number | null;
  modelType: ModelType;
  childIdentifier: string;
  endpoint: ApiEndpoints;
}>) {
  const api = useApi();
  const navigate = useNavigate();
  const treeState = useTree();

  const [searchValue, setSearchValue] = useState('');
  const [debouncedSearch] = useDebouncedValue(searchValue, 300);

  // Data query to fetch the tree data from server
  const query = useQuery({
    enabled: opened,
    queryKey: [modelType, opened, debouncedSearch],
    queryFn: async () => {
      const params: Record<string, any> = { ordering: 'level' };
      return api
        .get(apiUrl(endpoint), {
          params: {
            search: debouncedSearch || undefined,
            max_level: debouncedSearch ? undefined : 0
          }
        })
        .then((response) => response.data ?? []);
    }
  });

  // Expand all nodes when a search is active so ancestors are visible
  useEffect(() => {
    if (debouncedSearch) {
      treeState.expandAllNodes();
    }
  }, [debouncedSearch, query.data]);

  const follow = useCallback(
    (node: TreeNodeData, event?: any) => {
      const url = getDetailUrl(modelType, node.value);
      if (eventModified(event)) {
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

    if (!query || !query?.data?.length) {
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
      const hasChildren: boolean =
        (payload.hasChildren && (payload.node as any).children.length > 0) ||
        resolveItem(payload.node, childIdentifier);

      return (
        <Group
          p={3}
          gap='xs'
          justify='left'
          key={payload.node.value}
          wrap='nowrap'
          onClick={() => {
            if (payload.hasChildren) {
              treeState.toggleExpanded(payload.node.value);
            }
          }}
        >
          <Space w={10 * (payload.level - 1)} />
          <ActionIcon
            size='sm'
            variant='transparent'
            aria-label={`nav-tree-toggle-${payload.node.value}}`}
          >
            {hasChildren ? (
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
            c='var(--mantine-color-text)'
          >
            {payload.node.label}
          </Anchor>
        </Group>
      );
    },
    [treeState, childIdentifier, follow]
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
        <TextInput
          placeholder={t`Search...`}
          value={searchValue}
          onChange={(event) => setSearchValue(event.currentTarget.value)}
          leftSection={<IconSearch size={16} />}
          rightSection={
            searchValue ? (
              <ActionIcon
                size='sm'
                variant='transparent'
                onClick={() => setSearchValue('')}
                aria-label={t`Clear search`}
              >
                <IconX size={14} />
              </ActionIcon>
            ) : null
          }
        />
        <Divider />
        <LoadingOverlay visible={query.isFetching || query.isLoading} />
        {query.isError ? (
          <Alert color='red' title={t`Error`} icon={<IconExclamationCircle />}>
            {t`Error loading navigation tree.`}
          </Alert>
        ) : (
          <Tree data={data} tree={treeState} renderNode={renderNode} />
        )}
      </Stack>
    </Drawer>
  );
}
