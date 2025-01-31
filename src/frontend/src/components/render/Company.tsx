import { Text } from '@mantine/core';
import type { ReactNode } from 'react';

import { ModelType } from '../../enums/ModelType';
import { getDetailUrl } from '../../functions/urls';
import { type InstanceRenderInterface, RenderInlineModel } from './Instance';

/**
 * Inline rendering of a single Address instance
 */
export function RenderAddress({
  instance
}: Readonly<InstanceRenderInterface>): ReactNode {
  const text = [
    instance.country,
    instance.postal_code,
    instance.postal_city,
    instance.province,
    instance.line1,
    instance.line2
  ]
    .filter(Boolean)
    .join(', ');

  return <RenderInlineModel primary={instance.title} secondary={text} />;
}

/**
 * Inline rendering of a single Company instance
 */
export function RenderCompany(
  props: Readonly<InstanceRenderInterface>
): ReactNode {
  const { instance } = props;

  return (
    <RenderInlineModel
      {...props}
      image={instance.thumnbnail || instance.image}
      primary={instance.name}
      secondary={instance.description}
      url={
        props.link ? getDetailUrl(ModelType.company, instance.pk) : undefined
      }
    />
  );
}

/**
 * Inline rendering of a single Contact instance
 */
export function RenderContact({
  instance
}: Readonly<InstanceRenderInterface>): ReactNode {
  return <RenderInlineModel primary={instance.name} />;
}

/**
 * Inline rendering of a single SupplierPart instance
 */
export function RenderSupplierPart(
  props: Readonly<InstanceRenderInterface>
): ReactNode {
  const { instance } = props;
  const supplier = instance.supplier_detail ?? {};
  const part = instance.part_detail ?? {};

  return (
    <RenderInlineModel
      {...props}
      primary={supplier?.name}
      secondary={instance.SKU}
      image={
        part?.thumbnail ?? part?.image ?? supplier?.thumbnail ?? supplier?.image
      }
      suffix={
        part.full_name ? <Text size='sm'>{part.full_name}</Text> : undefined
      }
      url={
        props.link
          ? getDetailUrl(ModelType.supplierpart, instance.pk)
          : undefined
      }
    />
  );
}

/**
 * Inline rendering of a single ManufacturerPart instance
 */
export function RenderManufacturerPart(
  props: Readonly<InstanceRenderInterface>
): ReactNode {
  const { instance } = props;
  const part = instance.part_detail ?? {};
  const manufacturer = instance.manufacturer_detail ?? {};

  return (
    <RenderInlineModel
      {...props}
      primary={manufacturer.name}
      secondary={instance.MPN}
      suffix={
        part.full_name ? <Text size='sm'>{part.full_name}</Text> : undefined
      }
      image={manufacturer?.thumnbnail ?? manufacturer.image}
      url={
        props.link
          ? getDetailUrl(ModelType.manufacturerpart, instance.pk)
          : undefined
      }
    />
  );
}
