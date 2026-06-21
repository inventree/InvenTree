import { t } from '@lingui/core/macro';
import { Group, Text, type TreeNodeData, TreeSelect } from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import { IconChevronDown, IconChevronRight } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { FieldValues, UseControllerReturn } from 'react-hook-form';

import type { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { cancelEvent } from '@lib/functions/Events';
import type { ApiFormFieldType } from '@lib/types/Forms';
import { useApi } from '../../../contexts/ApiContext';

/**
 * A form field that renders a hierarchical tree selector backed by a tree API endpoint.
 * Supports server-side search: when the user types, the API is queried with the search term
 * and the backend returns matching nodes plus their ancestors for context.
 */
export function TreeField({
  controller,
  definition,
  fieldName,
  endpoint,
  childIdentifier
}: Readonly<{
  controller: UseControllerReturn<FieldValues, any>;
  definition: ApiFormFieldType;
  fieldName: string;
  endpoint: ApiEndpoints;
  childIdentifier: string;
}>) {
  const api = useApi();
  const {
    field,
    fieldState: { error }
  } = controller;

  // Keep the selected pk in sync with form state so we can always request
  // the selected node (and its ancestors) for label hydration.
  const selectedValue = useMemo(
    () => (field.value != null ? Number(field.value) : null),
    [field.value]
  );

  // Track dropdown state to separate server-side search text from the
  // read-only display label shown when the field is closed.
  const dropdownOpen = useRef(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // Track the pk whose ancestor path was last auto-expanded.
  const expandedForValue = useRef<number | null>(null);

  const [searchValue, setSearchValue] = useState('');
  const [debouncedSearch] = useDebouncedValue(searchValue, 300);
  const [expandedValues, setExpandedValues] = useState<string[]>([]);
  const [nodes, setNodes] = useState<any[]>([]);

  const query = useQuery({
    queryKey: [
      'tree-field',
      fieldName,
      endpoint,
      debouncedSearch,
      selectedValue
    ],
    queryFn: () =>
      api
        .get(apiUrl(endpoint), {
          params: {
            ...definition.filters,
            ordering: 'level',
            search: debouncedSearch || undefined,
            // Include the selected node and its ancestors in the initial response
            // so the node label is available before the user interacts with the field.
            expand_to:
              !debouncedSearch && !!selectedValue ? selectedValue : undefined,
            max_level: !debouncedSearch && !!selectedValue ? 0 : undefined
          }
        })
        .then((res) => res.data ?? [])
  });

  useEffect(() => {
    setNodes(query.data ?? []);
  }, [query.data]);

  // O(1) lookup for raw node data inside renderNode
  const nodeMap = useMemo(() => {
    const map: Record<string, any> = {};
    for (const n of nodes) map[n.pk.toString()] = n;
    return map;
  }, [nodes]);

  // Expand all returned nodes when a search is active so users can see all matches.
  // On the first browse-mode load, expand the ancestors of the initial value so
  // the tree shows the path to the currently-selected node.
  useEffect(() => {
    if (debouncedSearch) {
      setExpandedValues(nodes.map((n: any) => n.pk.toString()));
      return;
    }

    if (
      selectedValue != null &&
      expandedForValue.current !== selectedValue &&
      nodes.length > 0
    ) {
      expandedForValue.current = selectedValue;
      const map: Record<number, any> = {};
      for (const n of nodes) map[n.pk] = n;
      const toExpand: string[] = [];
      let cur = map[selectedValue];
      while (cur?.parent) {
        toExpand.push(String(cur.parent));
        cur = map[cur.parent];
      }
      setExpandedValues(toExpand);
      return;
    }

    if (selectedValue == null) {
      expandedForValue.current = null;
    }
  }, [debouncedSearch, nodes, selectedValue]);

  // Convert the flat API response (sorted by level) into the nested TreeNodeData structure.
  // `children` is intentionally left undefined on leaf nodes: Mantine's flatten logic uses
  // Array.isArray(node.children) to detect loaded children, so an empty [] would make every
  // node look like a parent. Instead we set node.hasChildren from the server-side count field
  // (childIdentifier) and only attach a children array when a child is actually encountered.
  const treeData: TreeNodeData[] = useMemo(() => {
    const map: Record<number, any> = {};
    const tree: TreeNodeData[] = [];

    const sorted = [...nodes].sort((a, b) => a.level - b.level);

    for (const raw of sorted) {
      const node: any = {
        value: raw.pk.toString(),
        label: raw.name as string,
        hasChildren: (raw[childIdentifier] ?? 0) > 0
      };

      map[raw.pk] = node;

      if (!raw.parent) {
        tree.push(node);
      } else if (map[raw.parent]) {
        if (!map[raw.parent].children) {
          map[raw.parent].children = [];
        }
        map[raw.parent].children.push(node);
      } else {
        // Keep orphaned nodes visible so selected labels can still resolve
        // if the API response omits an ancestor.
        tree.push(node);
      }
    }
    return tree;
  }, [nodes, childIdentifier]);

  const onChange = useCallback(
    (val: string | null) => {
      const pk = val ? Number.parseInt(val) : null;
      field.onChange(pk);
      definition.onValueChange?.(pk);
    },
    [field, definition]
  );

  const selectValue = useMemo(
    () => (field.value != null ? field.value.toString() : null),
    [field.value]
  );

  const selectedLabel = useMemo(() => {
    if (selectValue == null) return '';
    return nodeMap[selectValue]?.name ?? selectValue;
  }, [nodeMap, selectValue]);

  const inputSearchValue = isDropdownOpen ? searchValue : selectedLabel;

  const refreshChildren = useCallback(
    async (nodeValue: string) => {
      const pk = Number.parseInt(nodeValue, 10);
      if (Number.isNaN(pk)) return;

      const node = nodeMap[nodeValue];
      if (!node) return;

      const response = await api.get(apiUrl(endpoint), {
        params: {
          ...definition.filters,
          ordering: 'level',
          parent: pk,
          max_level: (node.level ?? 0) + 1
        }
      });

      const children: any[] = response.data ?? [];

      setNodes((prev) => {
        const base = prev.filter((n) => n.parent !== pk);
        const byPk = new Map<number, any>();

        for (const n of base) {
          byPk.set(n.pk, n);
        }

        for (const child of children) {
          byPk.set(child.pk, child);
        }

        if (children.length === 0) {
          const parentNode = byPk.get(pk);
          if (parentNode) {
            byPk.set(pk, { ...parentNode, [childIdentifier]: 0 });
          }
        }

        return Array.from(byPk.values());
      });
    },
    [api, endpoint, nodeMap, childIdentifier]
  );

  const toggleExpanded = useCallback(
    (nodeValue: string) => {
      setExpandedValues((prev) => {
        const isExpanded = prev.includes(nodeValue);

        if (!isExpanded) {
          void refreshChildren(nodeValue);
          return [...prev, nodeValue];
        }

        return prev.filter((v) => v !== nodeValue);
      });
    },
    [refreshChildren]
  );

  return (
    <TreeSelect
      data={treeData}
      value={selectValue}
      searchValue={inputSearchValue}
      onChange={onChange}
      onSearchChange={(val) => {
        if (dropdownOpen.current) setSearchValue(val);
      }}
      searchable
      filter={() => true}
      clearable={!definition.required}
      expandedValues={expandedValues}
      onExpandedChange={setExpandedValues}
      onDropdownOpen={() => {
        dropdownOpen.current = true;
        setIsDropdownOpen(true);
      }}
      onDropdownClose={() => {
        dropdownOpen.current = false;
        setIsDropdownOpen(false);
        setSearchValue('');
      }}
      label={definition.label}
      description={definition.description}
      placeholder={definition.placeholder ?? t`Select...`}
      required={definition.required}
      disabled={definition.disabled}
      error={definition.error ?? error?.message}
      comboboxProps={{ withinPortal: true }}
      maxDropdownHeight={300}
      nothingFoundMessage={
        query.isFetching ? t`Loading...` : t`No results found`
      }
      renderNode={({ node, expanded, hasChildren, selected }) => {
        const raw = nodeMap[node.value];
        return (
          <Group
            justify='space-between'
            gap='xs'
            wrap='nowrap'
            style={{ flex: 1 }}
          >
            <Group gap={4} wrap='nowrap'>
              {/* Chevron rendered manually so renderNode can coexist with expand behavior.
                  stopPropagation prevents the Combobox.Option from selecting the node
                  when the user clicks the expand toggle. */}
              <span
                style={{
                  display: 'inline-flex',
                  width: 16,
                  alignItems: 'center',
                  flexShrink: 0,
                  cursor: hasChildren ? 'pointer' : 'default'
                }}
                role={hasChildren ? 'button' : undefined}
                tabIndex={hasChildren ? -1 : undefined}
                aria-label={expanded ? t`Collapse` : t`Expand`}
                onClick={
                  hasChildren
                    ? (event: any) => {
                        cancelEvent(event);
                        toggleExpanded(node.value);
                      }
                    : undefined
                }
                onKeyDown={
                  hasChildren
                    ? (event: any) => {
                        if (event.key === 'Enter' || event.key === ' ') {
                          cancelEvent(event);
                          toggleExpanded(node.value);
                        }
                      }
                    : undefined
                }
              >
                {hasChildren &&
                  (expanded ? (
                    <IconChevronDown size={14} />
                  ) : (
                    <IconChevronRight size={14} />
                  ))}
              </span>
              <Text size='sm' fw={selected ? 600 : undefined}>
                {raw?.name ?? String(node.label)}
              </Text>
            </Group>
            {raw?.description && (
              <Text size='xs' c='dimmed' ta='right' truncate flex={1} maw='50%'>
                {raw.description}
              </Text>
            )}
          </Group>
        );
      }}
    />
  );
}
