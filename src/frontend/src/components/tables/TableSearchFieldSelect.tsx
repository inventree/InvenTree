import type { TableSearchField } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import {
  ActionIcon,
  Checkbox,
  Divider,
  Indicator,
  Menu,
  Tooltip
} from '@mantine/core';
import { IconListSearch } from '@tabler/icons-react';
import { useCallback } from 'react';

/**
 * Menu which allows the user to limit a table search to a subset of the searchable fields.
 *
 * The available fields are provided by the server (via the OPTIONS request for the table),
 * and the menu is only displayed if there is more than one field to choose from.
 *
 * An empty selection means "search all fields" (default behavior).
 */
export function TableSearchFieldSelect({
  fields,
  disabled,
  selectedFields,
  onChange
}: Readonly<{
  fields: TableSearchField[];
  disabled?: boolean;
  selectedFields: string[];
  onChange: (fields: string[]) => void;
}>) {
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

  // Selecting from a single field is the same as searching all fields
  if (fields.length <= 1) {
    return null;
  }

  return (
    <Indicator
      size='xs'
      label={selectedFields.length}
      disabled={selectedFields.length == 0}
    >
      <Menu shadow='xs' closeOnItemClick={false} position='bottom-end'>
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
          <Menu.Item key='all-search-fields'>
            <Checkbox
              aria-label='search-field-all'
              checked={selectedFields.length == 0}
              label={t`All fields`}
              onChange={() => onChange([])}
              radius='sm'
            />
          </Menu.Item>
          <Divider />
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
