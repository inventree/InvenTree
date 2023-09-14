import { t } from '@lingui/macro';
import { Alert } from '@mantine/core';
import { Group, Text } from '@mantine/core';
import { ReactNode } from 'react';

import { Thumbnail } from '../items/Thumbnail';
import { RenderBuildOrder } from './Build';
import {
  RenderAddress,
  RenderCompany,
  RenderContact,
  RenderSupplierPart
} from './Company';
import {
  RenderPurchaseOrder,
  RenderReturnOrder,
  RenderSalesOrder,
  RenderSalesOrderShipment
} from './Order';
import { RenderPart, RenderPartCategory } from './Part';
import { RenderStockItem, RenderStockLocation } from './Stock';
import { RenderOwner, RenderUser } from './User';

// import { ApiFormFieldType } from "../forms/fields/ApiFormField";

/**
 * Render an instance of a database model, depending on the provided data
 */
export function RenderInstance({
  model,
  instance
}: {
  model: string;
  instance: any;
}): ReactNode {
  switch (model) {
    case 'address':
      return <RenderAddress address={instance} />;
    case 'build':
      return <RenderBuildOrder buildorder={instance} />;
    case 'company':
      return <RenderCompany company={instance} />;
    case 'contact':
      return <RenderContact contact={instance} />;
    case 'owner':
      return <RenderOwner owner={instance} />;
    case 'part':
      return <RenderPart part={instance} />;
    case 'partcategory':
      return <RenderPartCategory category={instance} />;
    case 'purchaseorder':
      return <RenderPurchaseOrder order={instance} />;
    case 'returnorder':
      return <RenderReturnOrder order={instance} />;
    case 'salesoder':
      return <RenderSalesOrder order={instance} />;
    case 'salesordershipment':
      return <RenderSalesOrderShipment shipment={instance} />;
    case 'stocklocation':
      return <RenderStockLocation location={instance} />;
    case 'stockitem':
      return <RenderStockItem item={instance} />;
    case 'supplierpart':
      return <RenderSupplierPart supplierpart={instance} />;
    case 'user':
      return <RenderUser user={instance} />;
    default:
      // Unknown model
      return (
        <Alert color="red" title={t`Unknown model: ${model}`}>
          <></>
        </Alert>
      );
  }
}

/**
 * Helper function for rendering an inline model in a consistent style
 */
export function RenderInlineModel({
  primary,
  secondary,
  image,
  labels,
  url
}: {
  primary: string;
  secondary?: string;
  image?: string;
  labels?: string[];
  url?: string;
}): ReactNode {
  // TODO: Handle labels
  // TODO: Handle URL

  return (
    <Group spacing="xs">
      {image && Thumbnail({ src: image, size: 18 })}
      <Text size="sm">{primary}</Text>
      {secondary && <Text size="xs">{secondary}</Text>}
    </Group>
  );
}
