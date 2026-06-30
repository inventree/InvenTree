import {
  ApiEndpoints,
  ModelType,
  TagsList,
  apiUrl,
  formatDecimal
} from '@lib/index';
import { t } from '@lingui/core/macro';
import { Group, Stack, Text } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { useApi } from '../../../contexts/ApiContext';
import { formatDate, formatPriceRange } from '../../../defaults/formatters';
import { useInstance } from '../../../hooks/UseInstance';
import { ApiImage } from '../../images/ApiImage';
import { RenderRemoteInstance } from '../../render/Instance';
import { RenderUser } from '../../render/User';
import { AttributeGrid, type AttributeRow } from '../AttributeGrid';
import type { PreviewType } from '../PreviewType';

function PartPreviewContent({ instance }: Readonly<{ instance: any }>) {
  const api = useApi();

  const { instance: requirements } = useInstance({
    endpoint: ApiEndpoints.part_requirements,
    pk: instance?.pk,
    hasPrimaryKey: true,
    disabled: !instance?.pk,
    defaultValue: {}
  });

  const { data: parameters = [] } = useQuery({
    queryKey: ['part-preview-parameters', instance?.pk],
    enabled: !!instance?.pk,
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.parameter_list), {
          params: {
            model_type: ModelType.part,
            model_id: instance.pk,
            limit: 100
          }
        })
        .then((res) => res.data?.results ?? [])
  });

  const units = instance?.units ? ` ${instance.units}` : '';

  const stockItems: AttributeRow[] = useMemo(() => {
    const totalStock =
      requirements?.total_stock ?? instance?.total_in_stock ?? 0;
    const availableStock =
      requirements?.unallocated_stock ?? instance?.unallocated_stock ?? 0;
    const minStock = instance?.minimum_stock ?? 0;
    const ordering = requirements?.ordering ?? 0;
    const canBuild = requirements?.can_build ?? 0;
    const building = requirements?.building ?? 0;

    return !instance?.virtual
      ? [
          {
            label: t`In Stock`,
            value: formatDecimal(totalStock) + units
          },
          availableStock !== totalStock
            ? {
                label: t`Available`,
                value: formatDecimal(availableStock) + units
              }
            : null,
          minStock > 0
            ? { label: t`Minimum`, value: formatDecimal(minStock) + units }
            : null,
          instance?.purchaseable && ordering > 0
            ? { label: t`On Order`, value: formatDecimal(ordering) + units }
            : null,
          instance?.assembly && canBuild >= 0
            ? { label: t`Can Build`, value: formatDecimal(canBuild) }
            : null,
          building > 0
            ? { label: t`In Production`, value: formatDecimal(building) }
            : null
        ].filter((x): x is NonNullable<typeof x> => x !== null)
      : [];
  }, [requirements, instance, units]);

  const parameterItems: AttributeRow[] = parameters.map((param: any) => ({
    label: param.template_detail?.name,
    value:
      param.data +
      (param.template_detail?.units ? ` ${param.template_detail.units}` : '')
  }));

  const infoItems: AttributeRow[] = useMemo(() => {
    const priceRange = formatPriceRange(
      instance?.pricing_min,
      instance?.pricing_max
    );

    return [
      {
        label: t`Category`,
        value: instance?.category ? (
          <RenderRemoteInstance
            model={ModelType.partcategory}
            pk={instance.category}
          />
        ) : null
      },
      {
        label: t`Revision Of`,
        value: instance?.revision_of ? (
          <RenderRemoteInstance
            model={ModelType.part}
            pk={instance.revision_of}
          />
        ) : null
      },
      {
        label: t`Variant Of`,
        value: instance?.variant_of ? (
          <RenderRemoteInstance
            model={ModelType.part}
            pk={instance.variant_of}
          />
        ) : null
      },
      {
        label: t`Price Range`,
        value:
          instance?.pricing_min != null || instance?.pricing_max != null
            ? priceRange
            : null
      },
      {
        label: t`Creation Date`,
        value: instance?.creation_date
          ? formatDate(instance.creation_date)
          : null
      },
      {
        label: t`Created By`,
        value: instance?.creation_user_detail
          ? RenderUser({ instance: instance.creation_user_detail })
          : null
      }
    ];
  }, [instance]);

  return (
    <Stack gap='md'>
      <Group align='flex-start' gap='md'>
        <ApiImage
          src={
            instance?.image ||
            instance?.thumbnail ||
            '/static/img/blank_image.png'
          }
          w={80}
          h={80}
          fit='contain'
          radius='sm'
        />
        <Stack gap={2} style={{ flex: 1 }}>
          <Text fw={700} size='lg'>
            {instance?.full_name || instance?.name}
          </Text>
          {instance?.description && (
            <Text c='dimmed' size='sm'>
              {instance.description}
            </Text>
          )}
          {instance?.IPN && (
            <Group gap='xs'>
              <Text size='xs' c='dimmed'>
                {t`IPN`}:
              </Text>
              <Text size='xs' fw={500}>
                {instance.IPN}
              </Text>
            </Group>
          )}
          {instance?.revision && (
            <Group gap='xs'>
              <Text size='xs' c='dimmed'>
                {t`Revision`}:
              </Text>
              <Text size='xs' fw={500}>
                {instance.revision}
              </Text>
            </Group>
          )}
          {instance?.category_name && (
            <Group gap='xs'>
              <Text size='xs' c='dimmed'>
                {t`Category`}:
              </Text>
              <Text size='xs'>{instance?.category_name}</Text>
            </Group>
          )}
        </Stack>
      </Group>

      {instance?.tags?.length > 0 && <TagsList tags={instance.tags} />}

      <AttributeGrid title={t`Part Information`} items={infoItems} />
      {!instance?.virtual && (
        <AttributeGrid title={t`Stock Information`} items={stockItems} />
      )}
      <AttributeGrid title={t`Parameters`} items={parameterItems} />
    </Stack>
  );
}

export function PartPreviewComponent({
  instance,
  modelId
}: Readonly<{
  instance: any;
  modelId: number;
}>): PreviewType {
  return {
    title: instance?.full_name || instance?.name || `Part #${modelId}`,
    preview: <PartPreviewContent instance={instance} />
  };
}
