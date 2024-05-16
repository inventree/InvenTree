import { t } from '@lingui/macro';
import { Alert, Group, Space, Text } from '@mantine/core';
import { ReactNode } from 'react';

import { ModelType } from '../../enums/ModelType';
import { Thumbnail } from '../images/Thumbnail';
import { RenderBuildLine, RenderBuildOrder } from './Build';
import {
  RenderAddress,
  RenderCompany,
  RenderContact,
  RenderManufacturerPart,
  RenderSupplierPart
} from './Company';
import { RenderProjectCode } from './Generic';
import {
  RenderPurchaseOrder,
  RenderReturnOrder,
  RenderSalesOrder,
  RenderSalesOrderShipment
} from './Order';
import {
  RenderPart,
  RenderPartCategory,
  RenderPartParameterTemplate,
  RenderPartTestTemplate
} from './Part';
import { RenderPlugin } from './Plugin';
import { RenderLabelTemplate, RenderReportTemplate } from './Report';
import {
  RenderStockItem,
  RenderStockLocation,
  RenderStockLocationType
} from './Stock';
import { RenderOwner, RenderUser } from './User';

type EnumDictionary<T extends string | symbol | number, U> = {
  [K in T]: U;
};

/**
 * Lookup table for rendering a model instance
 */
const RendererLookup: EnumDictionary<
  ModelType,
  (props: Readonly<InstanceRenderInterface>) => ReactNode
> = {
  [ModelType.address]: RenderAddress,
  [ModelType.build]: RenderBuildOrder,
  [ModelType.buildline]: RenderBuildLine,
  [ModelType.company]: RenderCompany,
  [ModelType.contact]: RenderContact,
  [ModelType.manufacturerpart]: RenderManufacturerPart,
  [ModelType.owner]: RenderOwner,
  [ModelType.part]: RenderPart,
  [ModelType.partcategory]: RenderPartCategory,
  [ModelType.partparametertemplate]: RenderPartParameterTemplate,
  [ModelType.parttesttemplate]: RenderPartTestTemplate,
  [ModelType.projectcode]: RenderProjectCode,
  [ModelType.purchaseorder]: RenderPurchaseOrder,
  [ModelType.purchaseorderline]: RenderPurchaseOrder,
  [ModelType.returnorder]: RenderReturnOrder,
  [ModelType.salesorder]: RenderSalesOrder,
  [ModelType.salesordershipment]: RenderSalesOrderShipment,
  [ModelType.stocklocation]: RenderStockLocation,
  [ModelType.stocklocationtype]: RenderStockLocationType,
  [ModelType.stockitem]: RenderStockItem,
  [ModelType.stockhistory]: RenderStockItem,
  [ModelType.supplierpart]: RenderSupplierPart,
  [ModelType.user]: RenderUser,
  [ModelType.reporttemplate]: RenderReportTemplate,
  [ModelType.labeltemplate]: RenderLabelTemplate,
  [ModelType.pluginconfig]: RenderPlugin
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
  suffix?: ReactNode;
  image?: string;
  labels?: string[];
  url?: string;
}): ReactNode {
  // TODO: Handle labels
  // TODO: Handle URL

  return (
    <Group gap="xs" justify="space-between" wrap="nowrap">
      <Group gap="xs" justify="left" wrap="nowrap">
        {image && Thumbnail({ src: image, size: 18 })}
        <Text size="sm">{primary}</Text>
        {secondary && <Text size="xs">{secondary}</Text>}
      </Group>
      {suffix && (
        <>
          <Space />
          <div style={{ fontSize: 'xs', lineHeight: 'xs' }}>{suffix}</div>
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

export interface InstanceRenderInterface {
  instance: any;
}
