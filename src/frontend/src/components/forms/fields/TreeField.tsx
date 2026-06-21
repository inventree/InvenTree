import { t } from '@lingui/core/macro';
import { type TreeNodeData, TreeSelect } from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useState } from 'react';
import type { FieldValues, UseControllerReturn } from 'react-hook-form';

import type { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
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
  endpoint
}: Readonly<{
  controller: UseControllerReturn<FieldValues, any>;
  definition: ApiFormFieldType;
  fieldName: string;
  endpoint: ApiEndpoints;
}>) {
  const api = useApi();
  const {
    field,
    fieldState: { error }
  } = controller;

  const [searchValue, setSearchValue] = useState('');
  const [debouncedSearch] = useDebouncedValue(searchValue, 300);
  const [expandedValues, setExpandedValues] = useState<string[]>([]);

  const query = useQuery({
    queryKey: ['tree-field', fieldName, endpoint, debouncedSearch],
    queryFn: () =>
      api
        .get(apiUrl(endpoint), {
          params: {
            ordering: 'level',
            search: debouncedSearch || undefined
          }
        })
        .then((res) => res.data ?? [])
  });

  const nodes: any[] = useMemo(() => query.data ?? [], [query.data]);

  // Expand all returned nodes when a search is active so users can see all matches.
  // Collapse back to root when the search is cleared.
  useEffect(() => {
    if (debouncedSearch) {
      setExpandedValues(nodes.map((n: any) => n.pk.toString()));
    } else {
      setExpandedValues([]);
    }
  }, [debouncedSearch, nodes]);

  // Convert the flat API response (sorted by level) into the nested TreeNodeData structure.
  const treeData: TreeNodeData[] = useMemo(() => {
    const map: Record<number, TreeNodeData & { children: TreeNodeData[] }> = {};
    const tree: TreeNodeData[] = [];

    const sorted = [...nodes].sort((a, b) => a.level - b.level);

    for (const raw of sorted) {
      const node = {
        value: raw.pk.toString(),
        label: raw.name as string,
        children: [] as TreeNodeData[]
      };

      map[raw.pk] = node;

      if (!raw.parent) {
        tree.push(node);
      } else {
        map[raw.parent]?.children.push(node);
      }
    }

    return tree;
  }, [nodes]);

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

  return (
    <TreeSelect
      data={treeData}
      value={selectValue}
      onChange={onChange}
      searchValue={searchValue}
      onSearchChange={setSearchValue}
      searchable
      filter={() => true}
      clearable={!definition.required}
      expandedValues={expandedValues}
      onExpandedChange={setExpandedValues}
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
    />
  );
}
