import { ReactNode } from 'react';

import { RenderInlineModel } from './Instance';

/**
 * Inline rendering of a single Address instance
 */
export function RenderAddress({ address }: { address: any }): ReactNode {
  let text = [
    address.title,
    address.country,
    address.postal_code,
    address.postal_city,
    address.province,
    address.line1,
    address.line2
  ]
    .filter(Boolean)
    .join(', ');

  return (
    <RenderInlineModel
      primary={address.description}
      secondary={address.address}
    />
  );
}

/**
 * Inline rendering of a single Company instance
 */
export function RenderCompany({ company }: { company: any }): ReactNode {
  // TODO: Handle URL

  return (
    <RenderInlineModel
      image={company.thumnbnail || company.image}
      primary={company.name}
      secondary={company.description}
    />
  );
}

/**
 * Inline rendering of a single Contact instance
 */
export function RenderContact({ contact }: { contact: any }): ReactNode {
  return <RenderInlineModel primary={contact.name} />;
}

/**
 * Inline rendering of a single SupplierPart instance
 */
export function RenderSupplierPart({
  supplierpart
}: {
  supplierpart: any;
}): ReactNode {
  // TODO: Handle image
  // TODO: handle URL

  let supplier = supplierpart.supplier_detail ?? {};
  let part = supplierpart.part_detail ?? {};

  let text = supplierpart.SKU;

  if (supplier.name) {
    text = `${supplier.name} | ${text}`;
  }

  return <RenderInlineModel primary={text} secondary={part.full_name} />;
}
