import { t } from '@lingui/macro';
import { Alert, Space } from '@mantine/core';
import { Group, Text } from '@mantine/core';
import { ReactNode } from 'react';

import { Thumbnail } from '../images/Thumbnail';
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
import {
  RenderPart,
  RenderPartCategory,
  RenderPartParameterTemplate
} from './Part';
import { RenderStockItem, RenderStockLocation } from './Stock';
import { RenderOwner, RenderUser } from './User';

type EnumDictionary<T extends string | symbol | number, U> = {
  [K in T]: U;
};

/**
 * Lookup table for rendering a model instance
 */
const RendererLookup: EnumDictionary<
  ModelType,
  (props: { instance: any }) => ReactNode
> = {
  [ModelType.address]: RenderAddress,
  [ModelType.build]: RenderBuildOrder,
  [ModelType.company]: RenderCompany,
  [ModelType.contact]: RenderContact,
  [ModelType.owner]: RenderOwner,
  [ModelType.part]: RenderPart,
  [ModelType.partcategory]: RenderPartCategory,
  [ModelType.partparametertemplate]: RenderPartParameterTemplate,
  [ModelType.purchaseorder]: RenderPurchaseOrder,
  [ModelType.returnorder]: RenderReturnOrder,
  [ModelType.salesorder]: RenderSalesOrder,
  [ModelType.salesordershipment]: RenderSalesOrderShipment,
  [ModelType.stocklocation]: RenderStockLocation,
  [ModelType.stockitem]: RenderStockItem,
  [ModelType.supplierpart]: RenderSupplierPart,
  [ModelType.user]: RenderUser,
  [ModelType.manufacturerpart]: RenderPart
};

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
  if (model === undefined) {
    console.error('RenderInstance: No model provided');
    return <UnknownRenderer model={model} />;
  }

  const RenderComponent = RendererLookup[model];

  if (!RenderComponent) {
    console.error(`RenderInstance: No renderer for model ${model}`);
    return <UnknownRenderer model={model} />;
  }

  return <RenderComponent instance={instance} />;
}

/**
 * Helper function for rendering an inline model in a consistent style
 */
export function RenderInlineModel({
  primary,
  secondary,
  suffix,
  image,
  labels,
  url
}: {
  primary: string;
  secondary?: string;
  suffix?: string;
  image?: string;
  labels?: string[];
  url?: string;
}): ReactNode {
  // TODO: Handle labels
  // TODO: Handle URL

  return (
    <Group spacing="xs" position="apart">
      <Group spacing="xs" position="left">
        {image && Thumbnail({ src: image, size: 18 })}
        <Text size="sm">{primary}</Text>
        {secondary && <Text size="xs">{secondary}</Text>}
      </Group>
      {suffix && (
        <>
          <Space />
          <Text size="xs">{suffix}</Text>
        </>
      )}
    </Group>
  );
}

export function UnknownRenderer({
  model
}: {
  model: ModelType | undefined;
}): ReactNode {
  return (
    <Alert color="red" title={t`Unknown model: ${model}`}>
      <></>
    </Alert>
  );
}
