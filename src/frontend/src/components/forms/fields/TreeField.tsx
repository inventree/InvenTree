import { t } from '@lingui/core/macro';
import {
  ActionIcon,
  Group,
  Input,
  Text,
  type TreeNodeData,
  TreeSelect
} from '@mantine/core';
import { useDebouncedValue, useId } from '@mantine/hooks';
import {
  IconChevronDown,
  IconChevronRight,
  IconLink,
  IconX
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { memo, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { FieldValues, UseControllerReturn } from 'react-hook-form';
import type { NavigateFunction } from 'react-router-dom';

import type { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelInformationDict } from '@lib/enums/ModelInformation';
import type { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { cancelEvent } from '@lib/functions/Events';
import { getDetailUrl, navigateToLink } from '@lib/functions/Navigation';
import type { ApiFormFieldType } from '@lib/types/Forms';
import { useApi } from '../../../contexts/ApiContext';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../../../states/SettingsStates';
import { ScanButton } from '../../buttons/ScanButton';
import { ApiIcon } from '../../items/ApiIcon';
import Expand from '../../items/Expand';
import { ModelHoverCard } from '../../render/ModelHoverCard';

/**
 * A form field that renders a hierarchical tree selector backed by a tree API
 * endpoint. Supports server-side search, lazy child loading, and (when a model
 * type is provided) barcode scanning and a hover-card navigate link.
 */
function TreeFieldComponent({
  controller,
  definition,
  fieldName,
  endpoint,
  childIdentifier,
  genericPlaceholder,
  model,
  navigate
}: Readonly<{
  controller: UseControllerReturn<FieldValues, any>;
  definition: ApiFormFieldType;
  fieldName: string;
  endpoint: ApiEndpoints;
  childIdentifier: string;
  genericPlaceholder?: string;
  model?: ModelType;
  navigate?: NavigateFunction | null;
}>) {
  const api = useApi();
  const inputId = useId();
  const globalSettings = useGlobalSettingsState();
  const userSettings = useUserSettingsState();

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
    enabled:
      !definition.disabled &&
      !definition.hidden &&
      (isDropdownOpen || selectedValue != null),
    queryKey: [
      'tree-field',
      fieldName,
      endpoint,
      isDropdownOpen,
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
            max_level: debouncedSearch ? undefined : 0,
            expand_to: debouncedSearch
              ? undefined
              : (selectedValue ?? undefined)
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
      const pk = val ? Number.parseInt(val, 10) : null;
      const raw = val ? (nodeMap[val] ?? {}) : {};
      field.onChange(pk);
      definition.onValueChange?.(pk, raw);
    },
    [field, definition, nodeMap]
  );

  const selectValue = useMemo(
    () => (field.value != null ? field.value.toString() : null),
    [field.value]
  );

  const selectedLabel = useMemo(() => {
    if (selectValue == null) return '';
    const node = nodeMap[selectValue];
    return node?.pathstring ?? node?.name ?? selectValue;
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

  // --- Navigate / hovercard ---

  const detailUrl = useMemo(() => {
    if (!model || !selectedValue) return '';
    return getDetailUrl(model, selectedValue, true);
  }, [model, selectedValue]);

  const handleNavigate = useCallback(
    (e: any) => {
      if (navigate && detailUrl) navigateToLink(detailUrl, navigate, e);
    },
    [navigate, detailUrl]
  );

  // When a navigate model is present and a value is selected, swap out
  // Mantine's built-in clear button for a custom right section that holds
  // both a clear button and a link to the model detail page (with tooltip).
  const showNavigateSection = Boolean(model && selectedValue);

  const navigateRightSection = showNavigateSection ? (
    <Group gap={2} wrap='nowrap' style={{ paddingRight: 4 }}>
      {!definition.required && selectValue && (
        <ActionIcon
          variant='transparent'
          size='xs'
          color='dimmed'
          aria-label={t`Clear`}
          onClick={(e: any) => {
            cancelEvent(e);
            onChange(null);
          }}
        >
          <IconX size={12} />
        </ActionIcon>
      )}
      <ModelHoverCard model={model} pk={selectedValue} navigate={navigate}>
        <ActionIcon
          variant='transparent'
          size='xs'
          component='a'
          href={detailUrl || '#'}
          target='_blank'
          aria-label={t`View details`}
          onClick={handleNavigate}
        >
          <IconLink size={12} />
        </ActionIcon>
      </ModelHoverCard>
    </Group>
  ) : undefined;

  // --- Barcode scanning ---

  const modelInfo = useMemo(
    () => (model ? ModelInformationDict[model] : null),
    [model]
  );

  const addBarcodeField = useMemo(() => {
    if (!modelInfo?.supports_barcode) return false;
    if (!globalSettings.isSet('BARCODE_ENABLE')) return false;
    if (!userSettings.isSet('BARCODE_IN_FORM_FIELDS')) return false;
    return true;
  }, [modelInfo, globalSettings, userSettings]);

  const onBarcodeScan = useCallback(
    (_barcode: string, response: any) => {
      if (!model) return;
      const modelData = response?.[model] ?? null;
      if (modelData?.pk) {
        field.onChange(modelData.pk);
        definition.onValueChange?.(modelData.pk, modelData);
      }
    },
    [model, field, definition]
  );

  // --- Render ---

  return (
    <Input.Wrapper
      label={definition.label}
      description={definition.description}
      required={definition.required}
      error={definition.error ?? error?.message}
      id={inputId}
    >
      <Group wrap='nowrap' gap={3}>
        <Expand>
          <TreeSelect
            id={inputId}
            data={treeData}
            aria-label={`tree-field-${fieldName}`}
            value={selectValue}
            searchValue={inputSearchValue}
            onChange={onChange}
            onSearchChange={(val) => {
              if (dropdownOpen.current) setSearchValue(val);
            }}
            searchable
            filter={() => true}
            clearable={showNavigateSection ? false : !definition.required}
            rightSection={navigateRightSection}
            rightSectionPointerEvents={showNavigateSection ? 'all' : undefined}
            rightSectionWidth={
              showNavigateSection ? (definition.required ? 28 : 52) : undefined
            }
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
            placeholder={
              isDropdownOpen && selectedLabel
                ? selectedLabel
                : (definition.placeholder ?? genericPlaceholder ?? t`Select...`)
            }
            disabled={definition.disabled}
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
                    {/* Chevron rendered manually so renderNode can coexist with
                        expand behavior. stopPropagation prevents the
                        Combobox.Option from selecting the node when the user
                        clicks the expand toggle. */}
                    <span
                      role={hasChildren ? 'button' : undefined}
                      tabIndex={hasChildren ? 0 : undefined}
                      style={{
                        display: 'inline-flex',
                        width: 16,
                        alignItems: 'center',
                        flexShrink: 0,
                        cursor: hasChildren ? 'pointer' : 'default'
                      }}
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
                    {raw?.icon && <ApiIcon name={raw.icon} size={14} />}
                    <Text
                      size='sm'
                      fw={selected ? 600 : undefined}
                      fs={raw?.structural ? 'italic' : undefined}
                      c={raw?.structural ? 'dimmed' : undefined}
                    >
                      {raw?.name ?? String(node.label)}
                    </Text>
                  </Group>
                  {raw?.description && (
                    <Text
                      size='xs'
                      c='dimmed'
                      ta='right'
                      truncate
                      flex={1}
                      maw='50%'
                    >
                      {raw.description}
                    </Text>
                  )}
                </Group>
              );
            }}
          />
        </Expand>
        {addBarcodeField && (
          <ScanButton modelType={model} onScanSuccess={onBarcodeScan} />
        )}
      </Group>
    </Input.Wrapper>
  );
}

export const TreeField = memo(TreeFieldComponent);
