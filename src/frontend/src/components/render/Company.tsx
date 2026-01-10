import type { ReactNode } from 'react';

import { Text } from '@mantine/core';

import { ModelType } from '@lib/enums/ModelType';
import { getDetailUrl } from '@lib/functions/Navigation';
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

  const primary: string = instance.title || text;
  const secondary: string = !!instance.title ? text : '';

  const suffix: ReactNode = instance.primary ? (
    <Text size='xs'>Primary Address</Text>
  ) : null;

  return (
    <RenderInlineModel
      primary={primary}
      secondary={secondary}
      suffix={suffix}
    />
  );
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
      image={instance.thumbnail || instance.image}
      primary={instance.name}
      suffix={instance.description}
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

  const secondary: string = instance.SKU;
  let suffix: string = part?.full_name ?? '';

  // Display non-unitary pack quantities
  if (instance.pack_quantity && instance.pack_quantity_native != 1) {
    suffix += ` (${instance.pack_quantity})`;
  }

  return (
    <RenderInlineModel
      {...props}
      primary={supplier?.name}
      secondary={secondary}
      image={
        part?.thumbnail ?? part?.image ?? supplier?.thumbnail ?? supplier?.image
      }
      suffix={suffix}
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
      suffix={part.full_name}
      image={manufacturer?.thumbnail ?? manufacturer.image}
      url={
        props.link
          ? getDetailUrl(ModelType.manufacturerpart, instance.pk)
          : undefined
      }
    />
  );
}
