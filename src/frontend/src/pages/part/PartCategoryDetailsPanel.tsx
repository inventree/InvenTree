import { ModelType } from '@lib/enums/ModelType';
import { t } from '@lingui/core/macro';
import { Group, Skeleton } from '@mantine/core';
import { useMemo } from 'react';

import type { DetailsField } from '../../components/details/Details';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import { useParameterDetailsGrid } from '../../components/details/ParameterDetailsGrid';
import { ApiIcon } from '../../components/items/ApiIcon';

export function PartCategoryDetailsPanel({
  instance
}: Readonly<{
  instance: any;
}>) {
  const left: DetailsField[] = useMemo(
    () => [
      {
        type: 'text',
        name: 'name',
        label: t`Name`,
        copy: true,
        value_formatter: () => (
          <Group gap='xs'>
            {instance?.icon && <ApiIcon name={instance.icon} />}
            {instance?.name}
          </Group>
        )
      },
      {
        type: 'text',
        name: 'pathstring',
        label: t`Path`,
        icon: 'sitemap',
        copy: true,
        hidden: !instance?.pathstring
      },
      {
        type: 'text',
        name: 'description',
        label: t`Description`,
        copy: true
      },
      {
        type: 'link',
        name: 'parent',
        model_field: 'name',
        icon: 'location',
        label: t`Parent Category`,
        model: ModelType.partcategory,
        hidden: !instance?.parent
      },
      {
        type: 'boolean',
        name: 'starred',
        icon: 'notification',
        label: t`Subscribed`
      }
    ],
    [instance]
  );

  const right: DetailsField[] = useMemo(
    () => [
      {
        type: 'text',
        name: 'part_count',
        label: t`Parts`,
        icon: 'part',
        value_formatter: () => instance?.part_count || '0'
      },
      {
        type: 'text',
        name: 'subcategories',
        label: t`Subcategories`,
        icon: 'sitemap',
        hidden: !instance?.subcategories
      },
      {
        type: 'boolean',
        name: 'structural',
        label: t`Structural`,
        icon: 'sitemap'
      },
      {
        type: 'link',
        name: 'parent_default_location',
        label: t`Parent default location`,
        model: ModelType.stocklocation,
        hidden:
          !instance?.parent_default_location || !!instance?.default_location
      },
      {
        type: 'link',
        name: 'default_location',
        label: t`Default location`,
        model: ModelType.stocklocation,
        hidden: !instance?.default_location
      }
    ],
    [instance]
  );

  const parametersTable = useParameterDetailsGrid({
    model_type: ModelType.partcategory,
    model_id: instance?.pk
  });

  if (!instance?.pk) return <Skeleton />;

  return (
    <ItemDetailsGrid
      tables={[
        { item: instance, fields: left },
        { item: instance, fields: right },
        parametersTable
      ]}
    />
  );
}
