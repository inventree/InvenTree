import { t } from '@lingui/core/macro';
import { Grid, Skeleton, Stack } from '@mantine/core';
import { useMemo } from 'react';

import TagsList from '@lib/components/TagsList';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';

import {
  type DetailsField,
  DetailsTable
} from '../../components/details/Details';
import { DetailsImage } from '../../components/details/DetailsImage';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import { useParameterDetailsGrid } from '../../components/details/ParameterDetailsGrid';

export function SupplierPartDetailsPanel({
  instance,
  allowImageEdit = false,
  refreshInstance
}: Readonly<{
  instance: any;
  allowImageEdit?: boolean;
  refreshInstance?: () => void;
}>) {
  const data = useMemo(() => {
    if (!instance) return {};
    return {
      ...instance,
      manufacturer: instance.manufacturer || instance.manufacturer_detail?.pk,
      MPN: instance.MPN || instance.manufacturer_part_detail?.MPN,
      manufacturer_part:
        instance.manufacturer_part || instance.manufacturer_part_detail?.pk
    };
  }, [instance]);

  const tl: DetailsField[] = [
    {
      type: 'link',
      name: 'part',
      label: t`Internal Part`,
      model: ModelType.part,
      hidden: !instance?.part
    },
    {
      type: 'string',
      name: 'part_detail.IPN',
      label: t`IPN`,
      copy: true,
      hidden: !data.part_detail?.IPN,
      icon: 'serial'
    },
    {
      type: 'string',
      name: 'part_detail.description',
      label: t`Part Description`,
      copy: true,
      icon: 'info',
      hidden: !data.part_detail?.description
    },
    {
      type: 'link',
      external: true,
      name: 'link',
      label: t`External Link`,
      copy: true,
      hidden: !instance?.link
    },
    {
      type: 'string',
      name: 'note',
      label: t`Note`,
      copy: true,
      hidden: !instance?.note
    }
  ];

  const bl: DetailsField[] = [
    {
      type: 'link',
      name: 'supplier',
      label: t`Supplier`,
      model: ModelType.company,
      icon: 'suppliers',
      hidden: !instance?.supplier
    },
    {
      type: 'string',
      name: 'SKU',
      label: t`SKU`,
      copy: true,
      icon: 'reference'
    },
    {
      type: 'string',
      name: 'description',
      label: t`Description`,
      copy: true,
      hidden: !data.description
    },
    {
      type: 'link',
      name: 'manufacturer',
      label: t`Manufacturer`,
      model: ModelType.company,
      icon: 'manufacturers',
      hidden: !data.manufacturer
    },
    {
      type: 'link',
      name: 'manufacturer_part',
      model_field: 'MPN',
      label: t`Manufacturer Part`,
      model: ModelType.manufacturerpart,
      icon: 'reference',
      hidden: !data.manufacturer_part
    }
  ];

  const br: DetailsField[] = [
    {
      type: 'string',
      name: 'packaging',
      label: t`Packaging`,
      copy: true,
      hidden: !data.packaging
    },
    {
      type: 'string',
      name: 'pack_quantity',
      label: t`Pack Quantity`,
      copy: true,
      hidden: !data.pack_quantity,
      icon: 'packages'
    }
  ];

  const tr: DetailsField[] = [
    {
      type: 'number',
      name: 'in_stock',
      label: t`In Stock`,
      copy: true,
      icon: 'stock'
    },
    {
      type: 'number',
      name: 'on_order',
      label: t`On Order`,
      copy: true,
      icon: 'purchase_orders'
    },
    {
      type: 'number',
      name: 'available',
      label: t`Supplier Availability`,
      hidden: !data.availability_updated,
      copy: true,
      icon: 'packages'
    },
    {
      type: 'date',
      name: 'availability_updated',
      label: t`Availability Updated`,
      copy: true,
      hidden: !data.availability_updated,
      icon: 'calendar'
    }
  ];

  const parametersTable = useParameterDetailsGrid({
    model_type: ModelType.supplierpart,
    model_id: instance?.pk
  });

  if (!instance?.pk) return <Skeleton />;

  return (
    <ItemDetailsGrid
      tables={[
        { title: t`Supplier`, fields: bl, item: data },
        { title: t`Packaging`, fields: br, item: data },
        { title: t`Availability`, fields: tr, item: data },
        parametersTable
      ]}
    >
      <Stack gap='xs'>
        <Grid grow>
          <DetailsImage
            appRole={allowImageEdit ? UserRoles.part : undefined}
            src={instance?.part_detail?.image}
            apiPath={apiUrl(ApiEndpoints.part_list, instance?.part_detail?.pk)}
            pk={instance?.part_detail?.pk}
            refresh={refreshInstance}
          />
          <Grid.Col span={8}>
            <DetailsTable title={t`Part Details`} fields={tl} item={data} />
          </Grid.Col>
        </Grid>
        <TagsList tags={instance?.tags} />
      </Stack>
    </ItemDetailsGrid>
  );
}
