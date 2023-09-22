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
import { ModelType } from './ModelType';
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
  model: ModelType | undefined;
  instance: any;
}): ReactNode {
  switch (model) {
    case ModelType.address:
      return <RenderAddress address={instance} />;
    case ModelType.build:
      return <RenderBuildOrder buildorder={instance} />;
    case ModelType.company:
      return <RenderCompany company={instance} />;
    case ModelType.contact:
      return <RenderContact contact={instance} />;
    case ModelType.owner:
      return <RenderOwner owner={instance} />;
    case ModelType.part:
      return <RenderPart part={instance} />;
    case ModelType.partcategory:
      return <RenderPartCategory category={instance} />;
    case ModelType.purchaseorder:
      return <RenderPurchaseOrder order={instance} />;
    case ModelType.returnorder:
      return <RenderReturnOrder order={instance} />;
    case ModelType.salesorder:
      return <RenderSalesOrder order={instance} />;
    case ModelType.salesordershipment:
      return <RenderSalesOrderShipment shipment={instance} />;
    case ModelType.stocklocation:
      return <RenderStockLocation location={instance} />;
    case ModelType.stockitem:
      return <RenderStockItem item={instance} />;
    case ModelType.supplierpart:
      return <RenderSupplierPart supplierpart={instance} />;
    case ModelType.user:
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
