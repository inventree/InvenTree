import { Trans, t } from '@lingui/macro';
import {
  Box,
  CloseButton,
  Combobox,
  Group,
  Input,
  InputBase,
  ScrollArea,
  Select,
  Text,
  TextInput,
  useCombobox
} from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import { IconX } from '@tabler/icons-react';
import Fuse from 'fuse.js';
import { startTransition, useEffect, useMemo, useState } from 'react';
import { FieldValues, UseControllerReturn } from 'react-hook-form';

import { useIconState } from '../../../states/IconState';
import { ApiIcon } from '../../items/ApiIcon';
import { ApiFormFieldType } from './ApiFormField';

export default function IconField({
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

  const [searchValue, setSearchValue] = useState('');
  const [debouncedSearchValue] = useDebouncedValue(searchValue, 200);
  const [category, setCategory] = useState<string | null>(null);
  const [pack, setPack] = useState<string | null>(null);

  const categories = useMemo(
    () =>
      Array.from(
        new Set(
          icons
            .filter((i) => (pack !== null ? i.package === pack : true))
            .map((i) => i.category)
        )
      ).map((x) =>
        x === ''
          ? { value: '', label: t`Uncategorized` }
          : { value: x, label: x }
      ),
    [icons, pack]
  );
  const packs = useMemo(
    () => iconPacks.map((pack) => ({ value: pack.prefix, label: pack.name })),
    [iconPacks]
  );

  const applyFilters = (
    iconList: typeof icons,
    category: string | null,
    pack: string | null
  ) => {
    if (category === null && pack === null) return iconList;
    return iconList.filter(
      (i) =>
        (category !== null ? i.category === category : true) &&
        (pack !== null ? i.package === pack : true)
    );
  };

  const filteredIcons = useMemo(() => {
    if (!debouncedSearchValue) {
      return applyFilters(icons, category, pack);
    }

    const res = filter.search(debouncedSearchValue.trim()).map((r) => r.item);

    return applyFilters(res, category, pack);
  }, [debouncedSearchValue, filter, category, pack]);

  // Reset category when pack changes and the current category is not available in the new pack
  useEffect(() => {
    if (value === null) return;

    if (!categories.find((c) => c.value === category)) {
      setCategory(null);
    }
  }, [pack]);

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
        <Group gap={4}>
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
            onChange={(c) => startTransition(() => setCategory(c))}
            data={categories}
            comboboxProps={{ withinPortal: false }}
            clearable
            placeholder={t`Select category`}
          />

          <Select
            value={pack}
            onChange={(c) => startTransition(() => setPack(c))}
            data={packs}
            comboboxProps={{ withinPortal: false }}
            clearable
            placeholder={t`Select pack`}
          />
        </Group>

        <Text size="sm" c="dimmed" ta="center" mt={2}>
          <Trans>{filteredIcons.length} icons</Trans>
        </Text>

        <ScrollArea h={200} offsetScrollbars mt={6}>
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
