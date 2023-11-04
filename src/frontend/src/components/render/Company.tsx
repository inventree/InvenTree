import { ReactNode } from 'react';

import { RenderInlineModel } from './Instance';

/**
 * Inline rendering of a single Address instance
 */
export function RenderAddress({ instance }: { instance: any }): ReactNode {
  let text = [
    instance.title,
    instance.country,
    instance.postal_code,
    instance.postal_city,
    instance.province,
    instance.line1,
    instance.line2
  ]
    .filter(Boolean)
    .join(', ');

  return (
    <RenderInlineModel
      primary={instance.description}
      secondary={instance.address}
    />
  );
}

/**
 * Inline rendering of a single Company instance
 */
export function RenderCompany({ instance }: { instance: any }): ReactNode {
  // TODO: Handle URL

  return (
    <RenderInlineModel
      image={instance.thumnbnail || instance.image}
      primary={instance.name}
      secondary={instance.description}
    />
  );
}

/**
 * Inline rendering of a single Contact instance
 */
export function RenderContact({ instance }: { instance: any }): ReactNode {
  return <RenderInlineModel primary={instance.name} />;
}

/**
 * Inline rendering of a single SupplierPart instance
 */
export function RenderSupplierPart({ instance }: { instance: any }): ReactNode {
  // TODO: handle URL

  let supplier = instance.supplier_detail ?? {};
  let part = instance.part_detail ?? {};

  return (
    <RenderInlineModel
      primary={supplier?.name}
      secondary={instance.SKU}
      image={part?.thumbnail ?? part?.image}
      suffix={part.full_name}
    />
  );
}

/**
 * Inline rendering of a single ManufacturerPart instance
 */
export function RenderManufacturerPart({
  instance
}: {
  instance: any;
}): ReactNode {
  let part = instance.part_detail ?? {};
  let manufacturer = instance.manufacturer_detail ?? {};

  return (
    <RenderInlineModel
      primary={manufacturer.name}
      secondary={instance.MPN}
      suffix={part.full_name}
      image={manufacturer?.thumnbnail ?? manufacturer.image}
    />
  );
}
