import { t } from '@lingui/core/macro';
import { Grid, Skeleton, Stack } from '@mantine/core';
import { type ReactNode, useMemo } from 'react';

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
import { formatPriceRange } from '../../defaults/formatters';
import { useInstance } from '../../hooks/UseInstance';

export function PartDetailsPanel({
  instance,
  allowImageEdit = false,
  refreshInstance,
  additionalContent
}: Readonly<{
  instance: any;
  allowImageEdit?: boolean;
  refreshInstance?: () => void;
  additionalContent?: ReactNode;
}>) {
  const { instance: requirements, instanceQuery: requirementsQuery } =
    useInstance({
      endpoint: ApiEndpoints.part_requirements,
      pk: instance?.pk,
      hasPrimaryKey: true,
      disabled: !instance?.pk,
      defaultValue: {}
    });

  const { instance: serials } = useInstance({
    endpoint: ApiEndpoints.part_serial_numbers,
    pk: instance?.pk,
    hasPrimaryKey: true,
    disabled: !instance?.pk,
    defaultValue: {}
  });

  const data = useMemo(() => {
    if (!instance) return {};
    const d = { ...instance };
    d.total_in_stock =
      requirements?.total_stock ?? instance?.total_in_stock ?? 0;
    d.unallocated =
      requirements?.unallocated_stock ?? instance?.unallocated_stock ?? 0;
    d.ordering = requirements?.ordering ?? instance?.ordering ?? 0;
    d.required =
      (requirements?.required_for_build_orders ??
        instance?.required_for_build_orders ??
        0) +
      (requirements?.required_for_sales_orders ??
        instance?.required_for_sales_orders ??
        0);
    d.allocated =
      (requirements?.allocated_to_build_orders ??
        instance?.allocated_to_build_orders ??
        0) +
      (requirements?.allocated_to_sales_orders ??
        instance?.allocated_to_sales_orders ??
        0);
    d.can_build = requirements?.can_build ?? 0;
    if (serials?.latest) d.latest_serial_number = serials.latest;
    return d;
  }, [instance, requirements, serials]);

  const fetching = requirementsQuery?.isFetching ?? false;

  const tl: DetailsField[] = [
    { type: 'string', name: 'name', label: t`Name`, icon: 'part', copy: true },
    {
      type: 'string',
      name: 'IPN',
      label: t`IPN`,
      copy: true,
      hidden: !instance?.IPN
    },
    { type: 'string', name: 'description', label: t`Description`, copy: true },
    {
      type: 'link',
      name: 'variant_of',
      label: t`Variant of`,
      model: ModelType.part,
      model_field: 'full_name',
      hidden: !instance?.variant_of
    },
    {
      type: 'link',
      name: 'revision_of',
      label: t`Revision of`,
      model: ModelType.part,
      model_field: 'full_name',
      hidden: !instance?.revision_of
    },
    {
      type: 'string',
      name: 'revision',
      label: t`Revision`,
      hidden: !instance?.revision,
      copy: true
    },
    {
      type: 'link',
      name: 'category',
      label: t`Category`,
      model: ModelType.partcategory
    },
    {
      type: 'link',
      name: 'default_location',
      label: t`Default Location`,
      model: ModelType.stocklocation,
      hidden: !instance?.default_location
    },
    {
      type: 'link',
      name: 'category_default_location',
      label: t`Category Default Location`,
      model: ModelType.stocklocation,
      hidden: instance?.default_location || !instance?.category_default_location
    },
    {
      type: 'string',
      name: 'units',
      label: t`Units`,
      copy: true,
      hidden: !instance?.units
    },
    {
      type: 'string',
      name: 'keywords',
      label: t`Keywords`,
      copy: true,
      hidden: !instance?.keywords
    },
    {
      type: 'link',
      name: 'link',
      label: t`Link`,
      external: true,
      copy: true,
      hidden: !instance?.link
    }
  ];

  const tr: DetailsField[] = [
    {
      type: 'number',
      name: 'total_in_stock',
      unit: instance?.units,
      label: t`In Stock`,
      hidden: instance?.virtual
    },
    {
      type: 'progressbar',
      name: 'unallocated_stock',
      total: data.total_in_stock,
      progress: data.unallocated,
      label: t`Available Stock`,
      hidden: instance?.virtual || data.total_in_stock == data.unallocated
    },
    {
      type: 'number',
      name: 'ordering',
      label: t`On Order`,
      unit: instance?.units,
      hidden: !instance?.purchaseable || instance?.ordering <= 0
    },
    {
      type: 'number',
      name: 'required',
      label: t`Required for Orders`,
      unit: instance?.units,
      hidden: data.required <= 0,
      icon: 'stocktake'
    },
    {
      type: 'progressbar',
      name: 'allocated_to_build_orders',
      icon: 'manufacturers',
      total: requirements?.required_for_build_orders,
      progress: requirements?.allocated_to_build_orders,
      label: t`Allocated to Build Orders`,
      hidden:
        fetching ||
        (requirements?.required_for_build_orders <= 0 &&
          requirements?.allocated_to_build_orders <= 0)
    },
    {
      type: 'progressbar',
      icon: 'sales_orders',
      name: 'allocated_to_sales_orders',
      total: requirements?.required_for_sales_orders,
      progress: requirements?.allocated_to_sales_orders,
      label: t`Allocated to Sales Orders`,
      hidden:
        fetching ||
        (requirements?.required_for_sales_orders <= 0 &&
          requirements?.allocated_to_sales_orders <= 0)
    },
    {
      type: 'progressbar',
      name: 'building',
      label: t`In Production`,
      progress: requirements?.building,
      total: requirements?.scheduled_to_build,
      hidden:
        fetching ||
        (!requirements?.building && !requirements?.scheduled_to_build)
    },
    {
      type: 'number',
      name: 'can_build',
      unit: instance?.units,
      label: t`Can Build`,
      hidden: !instance?.assembly || fetching
    },
    {
      type: 'number',
      name: 'minimum_stock',
      unit: instance?.units,
      label: t`Minimum Stock`,
      hidden: instance?.minimum_stock <= 0
    },
    {
      type: 'number',
      name: 'maximum_stock',
      unit: instance?.units,
      label: t`Maximum Stock`,
      hidden: instance?.maximum_stock <= 0
    }
  ];

  const bl: DetailsField[] = [
    { type: 'boolean', name: 'active', label: t`Active` },
    { type: 'boolean', name: 'locked', label: t`Locked` },
    {
      type: 'boolean',
      icon: 'template',
      name: 'is_template',
      label: t`Template Part`
    },
    { type: 'boolean', name: 'assembly', label: t`Assembled Part` },
    { type: 'boolean', name: 'component', label: t`Component Part` },
    {
      type: 'boolean',
      name: 'testable',
      label: t`Testable Part`,
      icon: 'test'
    },
    { type: 'boolean', name: 'trackable', label: t`Trackable Part` },
    { type: 'boolean', name: 'purchaseable', label: t`Purchaseable Part` },
    {
      type: 'boolean',
      name: 'salable',
      icon: 'saleable',
      label: t`Saleable Part`
    },
    { type: 'boolean', name: 'virtual', label: t`Virtual Part` },
    { type: 'boolean', name: 'starred', label: t`Subscribed`, icon: 'bell' }
  ];

  const br: DetailsField[] = useMemo(() => {
    const fields: DetailsField[] = [
      {
        type: 'string',
        name: 'creation_date',
        label: t`Creation Date`
      },
      {
        type: 'string',
        name: 'creation_user',
        label: t`Created By`,
        badge: 'user',
        icon: 'user',
        hidden: !instance?.creation_user
      },
      {
        type: 'string',
        name: 'responsible',
        label: t`Responsible`,
        badge: 'owner',
        hidden: !instance?.responsible
      },
      {
        name: 'default_expiry',
        label: t`Default Expiry`,
        hidden: !instance?.default_expiry,
        icon: 'calendar',
        type: 'string',
        value_formatter: () => `${instance?.default_expiry} ${t`days`}`
      }
    ];

    if (instance?.pricing_min || instance?.pricing_max) {
      fields.push({
        type: 'string',
        name: 'pricing',
        label: t`Price Range`,
        value_formatter: () =>
          formatPriceRange(instance?.pricing_min, instance?.pricing_max)
      });
    }

    fields.push({
      type: 'string',
      name: 'latest_serial_number',
      label: t`Latest Serial Number`,
      hidden: !instance?.trackable || !data.latest_serial_number,
      icon: 'serial'
    });

    return fields;
  }, [instance, data.latest_serial_number]);

  const parametersTable = useParameterDetailsGrid({
    model_type: ModelType.part,
    model_id: instance?.pk
  });

  if (!instance?.pk) return <Skeleton />;

  return (
    <ItemDetailsGrid
      tables={[
        { fields: tr, item: data },
        { fields: bl, item: data },
        { fields: br, item: data },
        parametersTable
      ]}
    >
      <Stack gap='xs'>
        <Grid grow>
          <DetailsImage
            appRole={allowImageEdit ? UserRoles.part : undefined}
            imageActions={
              allowImageEdit
                ? {
                    selectExisting: true,
                    downloadImage: true,
                    uploadFile: true,
                    deleteFile: true
                  }
                : {}
            }
            src={instance.image}
            thumbnail={instance.thumbnail}
            apiPath={apiUrl(ApiEndpoints.part_list, instance.pk)}
            refresh={refreshInstance}
            pk={instance.pk}
          />
          <Grid.Col span={{ base: 12, sm: 8 }}>
            <DetailsTable fields={tl} item={data} />
          </Grid.Col>
        </Grid>
        <TagsList tags={instance.tags} />
        {additionalContent}
      </Stack>
    </ItemDetailsGrid>
  );
}
