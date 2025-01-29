import { Trans, t } from '@lingui/macro';
import {
  Box,
  CloseButton,
  Combobox,
  type ComboboxStore,
  Group,
  Input,
  InputBase,
  Select,
  Stack,
  Text,
  TextInput,
  useCombobox
} from '@mantine/core';
import { useDebouncedValue, useElementSize } from '@mantine/hooks';
import { IconX } from '@tabler/icons-react';
import Fuse from 'fuse.js';
import { startTransition, useEffect, useMemo, useRef, useState } from 'react';
import type { FieldValues, UseControllerReturn } from 'react-hook-form';
import { FixedSizeGrid as Grid } from 'react-window';

import { useIconState } from '../../../states/IconState';
import { ApiIcon } from '../../items/ApiIcon';
import type { ApiFormFieldType } from './ApiFormField';

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

  const [open, setOpen] = useState(false);
  const combobox = useCombobox({
    onOpenedChange: (opened) => setOpen(opened)
  });

  return (
    <Combobox store={combobox}>
      <Combobox.Target>
        <InputBase
          label={definition.label}
          description={definition.description}
          required={definition.required}
          error={definition.error ?? error?.message}
          ref={field.ref}
          component='button'
          type='button'
          pointer
          rightSection={
            value !== null && !definition.required ? (
              <CloseButton
                size='sm'
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
            <Group gap='xs'>
              <ApiIcon name={field.value} />
              <Text size='sm' c='dimmed'>
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
        <ComboboxDropdown
          definition={definition}
          value={value}
          combobox={combobox}
          onChange={field.onChange}
          open={open}
        />
      </Combobox.Dropdown>
    </Combobox>
  );
}

type RenderIconType = {
  package: string;
  name: string;
  tags: string[];
  category: string;
  variant: string;
};

function ComboboxDropdown({
  definition,
  value,
  combobox,
  onChange,
  open
}: Readonly<{
  definition: ApiFormFieldType;
  value: null | string;
  combobox: ComboboxStore;
  onChange: (newVal: string | null) => void;
  open: boolean;
}>) {
  const iconPacks = useIconState((s) => s.packages);
  const icons = useMemo<RenderIconType[]>(() => {
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
    iconList: RenderIconType[],
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

  const { width, ref } = useElementSize();

  return (
    <Stack gap={6} ref={ref}>
      <Group gap={4}>
        <TextInput
          value={searchValue}
          onChange={(e) => setSearchValue(e.currentTarget.value)}
          placeholder={t`Search...`}
          rightSection={
            searchValue && !definition.required ? (
              <IconX size='1rem' onClick={() => setSearchValue('')} />
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

      <Text size='sm' c='dimmed' ta='center' mt={-4}>
        <Trans>{filteredIcons.length} icons</Trans>
      </Text>

      <DropdownList
        icons={filteredIcons}
        onChange={onChange}
        combobox={combobox}
        value={value}
        width={width}
        open={open}
      />
    </Stack>
  );
}

function DropdownList({
  icons,
  onChange,
  combobox,
  value,
  width,
  open
}: Readonly<{
  icons: RenderIconType[];
  onChange: (newVal: string | null) => void;
  combobox: ComboboxStore;
  value: string | null;
  width: number;
  open: boolean;
}>) {
  // Get the inner width of the dropdown (excluding the scrollbar) by using the outerRef provided by the react-window Grid element
  const { width: innerWidth, ref: innerRef } = useElementSize();

  const columnCount = Math.floor(innerWidth / 35);
  const rowCount = columnCount > 0 ? Math.ceil(icons.length / columnCount) : 0;

  const gridRef = useRef<Grid>(null);
  const hasScrolledToPositionRef = useRef(true);

  // Reset the has already scrolled to position state when the dropdown open state is changed
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      hasScrolledToPositionRef.current = false;
    }, 100);

    return () => clearTimeout(timeoutId);
  }, [open]);

  // Scroll to the selected icon if not already has scrolled to position
  useEffect(() => {
    // Do not scroll if the value is not set, columnCount is not set, the dropdown is not open, or the position has already been scrolled to
    if (
      !value ||
      columnCount === 0 ||
      hasScrolledToPositionRef.current ||
      !open
    )
      return;

    const iconIdx = icons.findIndex((i) => i.name === value);
    if (iconIdx === -1) return;

    gridRef.current?.scrollToItem({
      align: 'start',
      rowIndex: Math.floor(iconIdx / columnCount)
    });
    hasScrolledToPositionRef.current = true;
  }, [value, columnCount, open]);

  return (
    <Grid
      height={200}
      width={width}
      rowCount={rowCount}
      columnCount={columnCount}
      rowHeight={35}
      columnWidth={35}
      itemData={icons}
      outerRef={innerRef}
      ref={gridRef}
    >
      {({ columnIndex, rowIndex, data, style }) => {
        const icon = data[rowIndex * columnCount + columnIndex];

        // Grid has empty cells in the last row if the number of icons is not a multiple of columnCount
        if (icon === undefined) return null;

        const isSelected = value === icon.name;

        return (
          <Box
            key={icon.name}
            title={icon.name}
            onClick={() => {
              onChange(isSelected ? null : icon.name);
              combobox.closeDropdown();
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              background: isSelected
                ? 'var(--mantine-color-blue-filled)'
                : 'unset',
              borderRadius: 'var(--mantine-radius-default)',
              ...style
            }}
          >
            <ApiIcon name={icon.name} size={24} />
          </Box>
        );
      }}
    </Grid>
  );
}
