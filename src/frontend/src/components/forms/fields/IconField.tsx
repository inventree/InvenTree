import { Trans, t } from '@lingui/macro';
import {
  ActionIcon,
  Box,
  Button,
  CloseButton,
  Combobox,
  Group,
  Input,
  InputBase,
  Popover,
  ScrollArea,
  Select,
  Text,
  TextInput,
  Tooltip,
  useCombobox
} from '@mantine/core';
import { useDebouncedValue, useScrollIntoView } from '@mantine/hooks';
import { IconX } from '@tabler/icons-react';
import Fuse from 'fuse.js';
import { useCallback, useEffect, useId, useMemo, useState } from 'react';
import { FieldValues, UseControllerReturn } from 'react-hook-form';

import { useIconState } from '../../../states/IconState';
import { ApiIcon } from '../../items/ApiIcon';
import { ApiFormFieldType } from './ApiFormField';

export default function IconField({
  controller,
  fieldName,
  definition
}: {
  controller: UseControllerReturn<FieldValues, any>;
  definition: ApiFormFieldType;
  fieldName: string;
}) {
  const {
    field,
    fieldState: { error }
  } = controller;

  const { value } = field;

  const combobox = useCombobox({});

  const iconPacks = useIconState((s) => s.packages);
  const icons = useMemo(() => {
    return iconPacks.flatMap((pack) =>
      Object.entries(pack.icons).flatMap(([name, icon]) =>
        Object.entries(icon.variants).map(([variant]) => ({
          package: pack.prefix,
          name: `${pack.prefix}:${name}:${variant}`,
          tags: icon.tags,
          category: icon.category,
          variant: variant
        }))
      )
    );
  }, [iconPacks]);
  const filter = useMemo(
    () =>
      new Fuse(icons, {
        threshold: 0.2,
        keys: ['name', 'tags', 'category', 'variant']
      }),
    [icons]
  );
  const categories = useMemo(
    () => Array.from(new Set(icons.map((i) => i.category))).filter((x) => !!x),
    [icons]
  );

  const [searchValue, setSearchValue] = useState('');
  const [debouncedSearchValue] = useDebouncedValue(searchValue, 200);
  const [category, setCategory] = useState<string | null>(null);

  const filteredIcons = useMemo(() => {
    if (!debouncedSearchValue) {
      if (!category) return icons;

      return icons.filter((i) => i.category === category);
    }

    const res = filter.search(debouncedSearchValue.trim()).map((r) => r.item);

    if (category) {
      return res.filter((i) =>
        category !== null ? i.category === category : true
      );
    }

    return res;
  }, [debouncedSearchValue, filter, category]);

  return (
    <Combobox store={combobox}>
      <Combobox.Target>
        <InputBase
          label={definition.label}
          description={definition.description}
          required={definition.required}
          error={error?.message}
          ref={field.ref}
          component="button"
          type="button"
          pointer
          rightSection={
            value !== null && !definition.required ? (
              <CloseButton
                size="sm"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => field.onChange(null)}
              />
            ) : (
              <Combobox.Chevron />
            )
          }
          onClick={() => combobox.toggleDropdown()}
          rightSectionPointerEvents={value === null ? 'none' : 'all'}
        >
          {field.value ? (
            <Group gap="xs">
              <ApiIcon name={field.value} />
              <Text size="sm" c="dimmed">
                {field.value}
              </Text>
            </Group>
          ) : (
            <Input.Placeholder>
              <Trans>No icon selected</Trans>
            </Input.Placeholder>
          )}
        </InputBase>
      </Combobox.Target>

      <Combobox.Dropdown>
        <Group mb={10} gap={4}>
          <TextInput
            value={searchValue}
            onChange={(e) => setSearchValue(e.currentTarget.value)}
            placeholder={t`Search...`}
            rightSection={
              searchValue && !definition.required ? (
                <IconX size="1rem" onClick={() => setSearchValue('')} />
              ) : null
            }
            flex={1}
          />
          <Select
            value={category}
            onChange={(c) => setCategory(c)}
            data={categories}
            comboboxProps={{ withinPortal: false }}
            clearable
            placeholder={t`Select category`}
          />
        </Group>

        <ScrollArea h={200} offsetScrollbars>
          <Group gap={2}>
            {filteredIcons.map((icon) => {
              const isSelected = field.value === icon.name;

              return (
                <Box
                  key={icon.name}
                  title={icon.name}
                  onClick={() => {
                    field.onChange(isSelected ? null : icon.name);
                    combobox.closeDropdown();
                  }}
                  style={{
                    cursor: 'pointer',
                    background: isSelected
                      ? 'var(--mantine-color-blue-5)'
                      : 'unset',
                    padding: 4,
                    borderRadius: 4
                  }}
                >
                  <ApiIcon name={icon.name} />
                </Box>
              );
            })}
          </Group>
        </ScrollArea>
      </Combobox.Dropdown>
    </Combobox>
  );
}
