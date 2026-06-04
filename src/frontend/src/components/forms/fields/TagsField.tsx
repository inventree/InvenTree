import { TagsInput } from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useState } from 'react';
import type { FieldValues, UseControllerReturn } from 'react-hook-form';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import type { ApiFormFieldType } from '@lib/types/Forms';
import { api } from '../../../App';

export default function TagsField({
  controller,
  definition
}: Readonly<{
  controller: UseControllerReturn<FieldValues, any>;
  definition: ApiFormFieldType;
}>) {
  const {
    field,
    fieldState: { error }
  } = controller;

  const [tags, setTags] = useState<string[]>(field.value ?? []);
  const [searchValue, setSearchValue] = useState('');
  const [debouncedSearch] = useDebouncedValue(searchValue, 250);

  // Sync inbound value changes (e.g. when initial data is loaded)
  useEffect(() => {
    setTags(field.value ?? []);
  }, [field.value]);

  const onChange = useCallback(
    (value: string[]) => {
      setTags(value);
      field.onChange(value);
      definition.onValueChange?.(value);
    },
    [field, definition]
  );

  const tagQuery = useQuery({
    queryKey: ['tags-autocomplete', debouncedSearch],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.tag_list), {
          params: { search: debouncedSearch, limit: 20 }
        })
        .then((r) => r.data)
  });

  const suggestions: string[] = useMemo(() => {
    const results: any[] = tagQuery.data?.results ?? tagQuery.data ?? [];
    return results.map((tag: any) => String(tag.name));
  }, [tagQuery.data]);

  const reducedDefinition: any = useMemo(() => {
    return {
      ...definition,
      allow_null: undefined,
      allow_blank: undefined
    };
  }, [definition]);

  return (
    <TagsInput
      {...reducedDefinition}
      ref={field.ref}
      placeholder={definition.placeholder}
      aria-label={`tags-field-${field.name}`}
      value={tags}
      onChange={onChange}
      data={suggestions}
      searchValue={searchValue}
      onSearchChange={setSearchValue}
      error={definition.error ?? error?.message}
      radius='sm'
      splitChars={[',', '\t', '\n', ';', ':', '.', '-']}
    />
  );
}
