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
  // TODO: Handle image
  // TODO: handle URL

  let supplier = instance.supplier_detail ?? {};
  let part = instance.part_detail ?? {};

  let text = instance.SKU;

  if (supplier.name) {
    text = `${supplier.name} | ${text}`;
  }

  return <RenderInlineModel primary={text} secondary={part.full_name} />;
}

/**
 * Inline rendering of a single ManufacturerPart instance
 */
export function ManufacturerPart({ instance }: { instance: any }): ReactNode {
  let supplier = instance.supplier_detail ?? {};
  let part = instance.part_detail ?? {};

  let text = instance.SKU;

  if (supplier.name) {
    text = `${supplier.name} | ${text}`;
  }

  return <RenderInlineModel primary={text} secondary={part.full_name} />;
}
