import {
  ActionIcon,
  Alert,
  Anchor,
  Divider,
  Drawer,
  Group,
  HoverCard,
  Loader,
  LoadingOverlay,
  type RenderTreeNodePayload,
  Space,
  Stack,
  Text,
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
  childIdentifier?: string;
  endpoint: ApiEndpoints;
}>) {
  const api = useApi();
  const navigate = useNavigate();
  const treeState = useTree();

  const [searchValue, setSearchValue] = useState('');
  const [debouncedSearch] = useDebouncedValue(searchValue, 300);

  // Accumulated flat node list for browse (lazy-load) mode
  const [allNodes, setAllNodes] = useState<any[]>([]);
  // PKs of nodes whose children are currently being fetched
  const [loadingNodes, setLoadingNodes] = useState<Set<number>>(new Set());

  // Reset everything when the drawer opens or closes
  useEffect(() => {
    setSearchValue('');
    setAllNodes([]);
    setLoadingNodes(new Set());
  }, [opened]);

  // Data query — browse mode loads root nodes only; search mode loads all matches + ancestors
  const query = useQuery({
    enabled: opened,
    queryKey: [modelType, 'tree', opened, debouncedSearch, selectedId],
    queryFn: async () =>
      api
        .get(apiUrl(endpoint), {
          params: {
            ordering: 'level',
            search: debouncedSearch || undefined,
            max_level: debouncedSearch ? undefined : 0,
            expand_to: debouncedSearch ? undefined : (selectedId ?? undefined)
          }
        })
        .then((response) => response.data ?? [])
  });

  // When the browse-mode query settles, reset the node list and expand ancestors of the selection
  useEffect(() => {
    if (!debouncedSearch && query.data && !query.isFetching) {
      setAllNodes(query.data);
      setLoadingNodes(new Set());

      if (selectedId) {
        const nodeMap: Record<number, any> = {};
        for (const n of query.data) nodeMap[n.pk] = n;

        // Collect every ancestor pk, then apply in one setExpandedState call to
        // avoid closure/batching issues that arise from calling expand() in a loop.
        const toExpand: Record<string, boolean> = {};
        let current = nodeMap[selectedId];
        while (current?.parent) {
          toExpand[current.parent.toString()] = true;
          current = nodeMap[current.parent];
        }
        if (Object.keys(toExpand).length) {
          treeState.setExpandedState({
            ...treeState.expandedState,
            ...toExpand
          });
        }
      }
    }
  }, [debouncedSearch, query.data, query.isFetching, selectedId]);

  // Collapse all nodes when the search term changes (switching modes).
  // Intentionally omits query.data so it does NOT fire when browse results arrive —
  // that would undo the ancestor expansion done above.
  useEffect(() => {
    treeState.collapseAllNodes();
  }, [debouncedSearch]);

  // Expand all nodes once search results have fully arrived
  useEffect(() => {
    if (debouncedSearch && !query.isFetching && query.data?.length) {
      treeState.expandAllNodes();
    }
  }, [debouncedSearch, query.data, query.isFetching]);

  // Fetch direct children of a node (browse mode only).
  // Zeros out the childIdentifier count on success with no results so the node
  // is treated as a leaf and won't be re-fetched on subsequent clicks.
  const fetchChildren = useCallback(
    async (nodeValue: string) => {
      const pk = Number.parseInt(nodeValue);
      if (loadingNodes.has(pk)) return;

      const nodeInfo = allNodes.find((n) => n.pk === pk);
      if (!nodeInfo) return;

      setLoadingNodes((prev) => new Set([...prev, pk]));

      try {
        const response = await api.get(apiUrl(endpoint), {
          params: {
            ordering: 'level',
            parent: pk,
            max_level: nodeInfo.level + 1
          }
        });
        const children: any[] = response.data ?? [];

        setAllNodes((prev) => {
          if (children.length === 0 && childIdentifier) {
            // No children returned — zero out the count so this node is treated
            // as a leaf and won't trigger another fetch on the next click.
            return prev.map((n) =>
              n.pk === pk ? { ...n, [childIdentifier]: 0 } : n
            );
          }
          const existing = new Set(prev.map((n) => n.pk));
          return [...prev, ...children.filter((n) => !existing.has(n.pk))];
        });

        if (children.length > 0) {
          treeState.expand(nodeValue);
        }
      } finally {
        setLoadingNodes((prev) => {
          const next = new Set(prev);
          next.delete(pk);
          return next;
        });
      }
    },
    [loadingNodes, allNodes, api, endpoint, childIdentifier]
  );

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

  // In search mode use the query results directly; in browse mode use the accumulated lazy-load list
  const sourceNodes: any[] = useMemo(
    () => (debouncedSearch ? (query.data ?? []) : allNodes),
    [debouncedSearch, query.data, allNodes]
  );

  // Map flat node list to a nested tree structure (parents must precede children)
  const data: TreeNodeData[] = useMemo(() => {
    const nodes: Record<number, any> = {};
    const tree: TreeNodeData[] = [];

    if (!sourceNodes.length) return [];

    // Sort by level so parents are always inserted before their children,
    // regardless of the order the API returns items (e.g. after ancestor union in search mode).
    const sorted = [...sourceNodes].sort((a, b) => a.level - b.level);

    for (const raw of sorted) {
      const node = {
        ...raw,
        children: [],
        label: (
          <Group gap='xs'>
            <ApiIcon name={raw.icon} />
            <Text>{raw.name}</Text>
          </Group>
        ),
        value: raw.pk.toString(),
        selected: raw.pk === selectedId
      };

      const pk: number = node.pk;
      const parent: number | null = node.parent;

      if (!parent) {
        tree.push(node);
      } else {
        nodes[parent]?.children.push(node);
      }

      nodes[pk] = node;
    }

    return tree;
  }, [selectedId, sourceNodes]);

  const renderNode = useCallback(
    (payload: RenderTreeNodePayload) => {
      const nodeInfo = payload.node as any;
      const pk = Number.parseInt(payload.node.value);
      const isLoading = loadingNodes.has(pk);

      // A node has children if they are already in the tree, or if the server-side
      // count (childIdentifier) says so and they haven't been loaded yet.
      const childrenLoaded = nodeInfo.children.length > 0;
      const needsFetch =
        !isLoading &&
        !debouncedSearch &&
        !childrenLoaded &&
        !!(childIdentifier && resolveItem(payload.node, childIdentifier));
      const hasChildren = childrenLoaded || needsFetch;

      const isSelected = nodeInfo.selected === true;

      return (
        <Group
          p={3}
          gap='xs'
          justify='left'
          key={payload.node.value}
          wrap='nowrap'
          bg={isSelected ? 'var(--mantine-primary-color-light)' : undefined}
          style={{ borderRadius: 'var(--mantine-radius-sm)' }}
          onClick={() => {
            if (isLoading || !hasChildren) return;
            if (needsFetch) {
              fetchChildren(payload.node.value);
            } else {
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
            {isLoading ? (
              <Loader size='xs' />
            ) : hasChildren ? (
              payload.expanded ? (
                <IconChevronDown />
              ) : (
                <IconChevronRight />
              )
            ) : null}
          </ActionIcon>
          <HoverCard
            width={260}
            shadow='md'
            withArrow
            closeDelay={100}
            openDelay={500}
            position='top-end'
          >
            <HoverCard.Target>
              <Anchor
                onClick={(event: any) => follow(payload.node, event)}
                aria-label={`nav-tree-item-${payload.node.value}`}
                c='var(--mantine-color-text)'
              >
                {payload.node.label}
              </Anchor>
            </HoverCard.Target>
            <HoverCard.Dropdown>
              <Stack gap={4}>
                <Group gap='xs' wrap='nowrap'>
                  {nodeInfo.icon && <ApiIcon name={nodeInfo.icon} />}
                  <Text fw={600} size='sm'>
                    {nodeInfo.name}
                  </Text>
                </Group>
                {nodeInfo.description && (
                  <Text size='sm' c='dimmed'>
                    {nodeInfo.description}
                  </Text>
                )}
              </Stack>
            </HoverCard.Dropdown>
          </HoverCard>
        </Group>
      );
    },
    [
      treeState,
      childIdentifier,
      follow,
      loadingNodes,
      fetchChildren,
      debouncedSearch
    ]
  );

  return (
    <Drawer
      opened={opened}
      size='lg'
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
        ) : !query.isFetching && !query.isLoading && data.length === 0 ? (
          <Alert color='blue' icon={<IconSearch />}>
            {t`No results found`}
          </Alert>
        ) : (
          <Tree data={data} tree={treeState} renderNode={renderNode} />
        )}
      </Stack>
    </Drawer>
  );
}
