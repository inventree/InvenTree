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
  // PKs of nodes whose children have already been fetched
  const [fetchedNodes, setFetchedNodes] = useState<Set<number>>(new Set());

  // Reset everything when the drawer closes
  useEffect(() => {
    setSearchValue('');
    setAllNodes([]);
    setFetchedNodes(new Set());
  }, [opened]);

  // Data query — browse mode loads root nodes only; search mode loads all matches + ancestors
  const query = useQuery({
    enabled: opened,
    queryKey: [modelType, 'tree', opened, debouncedSearch],
    queryFn: async () =>
      api
        .get(apiUrl(endpoint), {
          params: {
            ordering: 'level',
            search: debouncedSearch || undefined,
            max_level: debouncedSearch ? undefined : 0
          }
        })
        .then((response) => response.data ?? [])
  });

  // When the browse-mode query settles, reset accumulated node list
  useEffect(() => {
    if (!debouncedSearch && query.data && !query.isFetching) {
      setAllNodes(query.data);
      setFetchedNodes(new Set());
    }
  }, [debouncedSearch, query.data, query.isFetching]);

  // Expand all nodes when a search is active so ancestors are visible
  useEffect(() => {
    if (debouncedSearch) {
      treeState.expandAllNodes();
    } else {
      treeState.collapseAllNodes();
    }
  }, [debouncedSearch, query.data]);

  // Fetch direct children of a node (browse mode only); no-op if already fetched
  const fetchChildren = useCallback(
    async (nodeValue: string) => {
      const pk = Number.parseInt(nodeValue);
      if (fetchedNodes.has(pk)) return;

      const nodeInfo = allNodes.find((n) => n.pk === pk);
      if (!nodeInfo) return;

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
          const existing = new Set(prev.map((n) => n.pk));
          return [...prev, ...children.filter((n) => !existing.has(n.pk))];
        });
      } finally {
        // Mark as fetched even on error so we don't retry on every click
        setFetchedNodes((prev) => new Set([...prev, pk]));
      }
    },
    [fetchedNodes, allNodes, api, endpoint]
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

    for (const raw of sourceNodes) {
      const node = {
        ...raw,
        children: [],
        label: (
          <Group gap='xs'>
            <ApiIcon name={raw.icon} />
            {raw.name}
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

      if (pk === selectedId) {
        let p = nodes[node.parent];
        while (p) {
          p.expanded = true;
          p = nodes[p.parent];
        }
      }
    }

    return tree;
  }, [selectedId, sourceNodes]);

  const renderNode = useCallback(
    (payload: RenderTreeNodePayload) => {
      const nodeInfo = payload.node as any;
      const pk = Number.parseInt(payload.node.value);
      const isFetched = fetchedNodes.has(pk);

      // Before children are fetched, use the server-provided count (childIdentifier field).
      // After fetching (or in search mode where all data is already present), use actual children.
      const hasChildren: boolean =
        !debouncedSearch && !isFetched
          ? !!resolveItem(payload.node, childIdentifier ?? '')
          : nodeInfo.children.length > 0;

      return (
        <Group
          p={3}
          gap='xs'
          justify='left'
          key={payload.node.value}
          wrap='nowrap'
          onClick={() => {
            if (!hasChildren) return;
            if (!debouncedSearch && !isFetched) {
              fetchChildren(payload.node.value);
            }
            treeState.toggleExpanded(payload.node.value);
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
    [
      treeState,
      childIdentifier,
      follow,
      fetchedNodes,
      fetchChildren,
      debouncedSearch
    ]
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
