import { t } from '@lingui/core/macro';
import { Group, Skeleton } from '@mantine/core';

import { ModelType } from '@lib/enums/ModelType';

import type { DetailsField } from '../../components/details/Details';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import { useParameterDetailsGrid } from '../../components/details/ParameterDetailsGrid';
import { ApiIcon } from '../../components/items/ApiIcon';

export function StockLocationDetailsPanel({
  instance
}: Readonly<{
  instance: any;
}>) {
  const left: DetailsField[] = [
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
      copy: true,
      hidden: !instance?.description
    },
    {
      type: 'link',
      name: 'parent',
      model_field: 'name',
      icon: 'location',
      label: t`Parent Location`,
      model: ModelType.stocklocation,
      hidden: !instance?.parent
    }
  ];

  const right: DetailsField[] = [
    {
      type: 'text',
      name: 'items',
      icon: 'stock',
      label: t`Stock Items`,
      value_formatter: () => instance?.items || '0'
    },
    {
      type: 'text',
      name: 'sublocations',
      icon: 'location',
      label: t`Sublocations`,
      hidden: !instance?.sublocations
    },
    {
      type: 'boolean',
      name: 'structural',
      label: t`Structural`,
      icon: 'sitemap'
    },
    {
      type: 'boolean',
      name: 'external',
      label: t`External`
    },
    {
      type: 'string',
      name: 'location_type_detail.name',
      label: t`Location Type`,
      hidden: !instance?.location_type,
      icon: 'packages'
    }
  ];

  const parametersTable = useParameterDetailsGrid({
    model_type: ModelType.stocklocation,
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
