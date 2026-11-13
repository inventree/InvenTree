import { t } from '@lingui/core/macro';
import {
  ActionIcon,
  Checkbox,
  Divider,
  Indicator,
  Loader,
  Menu,
  Text,
  Tooltip
} from '@mantine/core';
import { IconListSearch } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import type { AxiosInstance } from 'axios';
import { useCallback, useState } from 'react';

export type TableSearchField = {
  name: string;
  label: string;
};

/**
 * Menu which allows the user to limit a table search to a subset of the searchable fields.
 *
 * The available fields are provided by the server (via an OPTIONS request),
 * and are only requested when the menu is first opened.
 *
 * An empty selection means "search all fields" (default behavior).
 */
export function TableSearchFieldSelect({
  api,
  url,
  disabled,
  selectedFields,
  onChange
}: Readonly<{
  api: AxiosInstance;
  url: string;
  disabled?: boolean;
  selectedFields: string[];
  onChange: (fields: string[]) => void;
}>) {
  const [opened, setOpened] = useState<boolean>(false);

  const fieldQuery = useQuery<TableSearchField[]>({
    enabled: opened && !!url,
    queryKey: ['table-search-fields', url],
    staleTime: 5 * 60 * 1000,
    queryFn: async () => {
      return api
        .options(url)
        .then((response) => response.data?.search_fields ?? [])
        .catch(() => []);
    }
  });

  const toggleField = useCallback(
    (name: string) => {
      if (selectedFields.includes(name)) {
        onChange(selectedFields.filter((field) => field != name));
      } else {
        onChange([...selectedFields, name]);
      }
    },
    [selectedFields, onChange]
  );

  const fields: TableSearchField[] = fieldQuery.data ?? [];

  return (
    <Indicator
      size='xs'
      label={selectedFields.length}
      disabled={selectedFields.length == 0}
    >
      <Menu
        shadow='xs'
        closeOnItemClick={false}
        opened={opened}
        onChange={setOpened}
        position='bottom-end'
      >
        <Menu.Target>
          <ActionIcon
            variant='transparent'
            disabled={disabled}
            aria-label='table-select-search-fields'
          >
            <Tooltip label={t`Select search fields`} position='top-end'>
              <IconListSearch />
            </Tooltip>
          </ActionIcon>
        </Menu.Target>
        <Menu.Dropdown style={{ maxHeight: '400px', overflowY: 'auto' }}>
          <Menu.Label>{t`Search in fields`}</Menu.Label>
          <Divider />
          {fieldQuery.isFetching && fields.length == 0 && (
            <Menu.Item disabled leftSection={<Loader size='xs' />}>
              {t`Loading`}
            </Menu.Item>
          )}
          {!fieldQuery.isFetching && fields.length == 0 && (
            <Menu.Item disabled>
              <Text size='sm'>{t`No searchable fields available`}</Text>
            </Menu.Item>
          )}
          {fields.length > 0 && (
            <Menu.Item key='all-search-fields'>
              <Checkbox
                aria-label='search-field-all'
                checked={selectedFields.length == 0}
                label={t`All fields`}
                onChange={() => onChange([])}
                radius='sm'
              />
            </Menu.Item>
          )}
          {fields.length > 0 && <Divider />}
          {fields.map((field) => (
            <Menu.Item key={field.name}>
              <Checkbox
                aria-label={`search-field-${field.name}`}
                checked={selectedFields.includes(field.name)}
                label={field.label || field.name}
                onChange={() => toggleField(field.name)}
                radius='sm'
              />
            </Menu.Item>
          ))}
        </Menu.Dropdown>
      </Menu>
    </Indicator>
  );
}
