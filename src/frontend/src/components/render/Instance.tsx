import { t } from '@lingui/core/macro';
import { Alert, Skeleton, Text } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import type { ReactNode } from 'react';

import { ModelInformationDict } from '@lib/enums/ModelInformation';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import type {
  ModelRendererDict,
  RemoteInstanceProps,
  RenderInstanceProps
} from '@lib/types/Rendering';
export type { InstanceRenderInterface } from '@lib/types/Rendering';
import { useApi } from '../../contexts/ApiContext';
import { RenderBuildItem, RenderBuildLine, RenderBuildOrder } from './Build';
import {
  RenderAddress,
  RenderCompany,
  RenderContact,
  RenderManufacturerPart,
  RenderSupplierPart
} from './Company';
import {
  RenderContentType,
  RenderError,
  RenderImportSession,
  RenderParameter,
  RenderParameterTemplate,
  RenderProjectCode,
  RenderSelectionEntry,
  RenderSelectionList
} from './Generic';
import {
  RenderPurchaseOrder,
  RenderReturnOrder,
  RenderReturnOrderLineItem,
  RenderSalesOrder,
  RenderSalesOrderShipment
} from './Order';
import { RenderPart, RenderPartCategory, RenderPartTestTemplate } from './Part';
import { RenderPlugin } from './Plugin';
import { RenderLabelTemplate, RenderReportTemplate } from './Report';
import {
  RenderStockItem,
  RenderStockLocation,
  RenderStockLocationType
} from './Stock';
import { RenderGroup, RenderOwner, RenderUser } from './User';

/**
 * Lookup table for rendering a model instance
 */
export const RendererLookup: ModelRendererDict = {
  [ModelType.address]: RenderAddress,
  [ModelType.build]: RenderBuildOrder,
  [ModelType.buildline]: RenderBuildLine,
  [ModelType.builditem]: RenderBuildItem,
  [ModelType.company]: RenderCompany,
  [ModelType.contact]: RenderContact,
  [ModelType.parameter]: RenderParameter,
  [ModelType.parametertemplate]: RenderParameterTemplate,
  [ModelType.manufacturerpart]: RenderManufacturerPart,
  [ModelType.owner]: RenderOwner,
  [ModelType.part]: RenderPart,
  [ModelType.partcategory]: RenderPartCategory,
  [ModelType.parttesttemplate]: RenderPartTestTemplate,
  [ModelType.projectcode]: RenderProjectCode,
  [ModelType.purchaseorder]: RenderPurchaseOrder,
  [ModelType.purchaseorderlineitem]: RenderPurchaseOrder,
  [ModelType.returnorder]: RenderReturnOrder,
  [ModelType.returnorderlineitem]: RenderReturnOrderLineItem,
  [ModelType.salesorder]: RenderSalesOrder,
  [ModelType.salesordershipment]: RenderSalesOrderShipment,
  [ModelType.stocklocation]: RenderStockLocation,
  [ModelType.stocklocationtype]: RenderStockLocationType,
  [ModelType.stockitem]: RenderStockItem,
  [ModelType.stockhistory]: RenderStockItem,
  [ModelType.supplierpart]: RenderSupplierPart,
  [ModelType.user]: RenderUser,
  [ModelType.group]: RenderGroup,
  [ModelType.importsession]: RenderImportSession,
  [ModelType.reporttemplate]: RenderReportTemplate,
  [ModelType.labeltemplate]: RenderLabelTemplate,
  [ModelType.pluginconfig]: RenderPlugin,
  [ModelType.contenttype]: RenderContentType,
  [ModelType.selectionlist]: RenderSelectionList,
  [ModelType.selectionentry]: RenderSelectionEntry,
  [ModelType.error]: RenderError
};

/**
 * Render an instance of a database model, depending on the provided data
 */
export function RenderInstance(props: RenderInstanceProps): ReactNode {
  if (props.model === undefined) {
    return <UnknownRenderer model={props.model} />;
  }

  const model_name = props.model.toString().toLowerCase() as ModelType;

  const RenderComponent = RendererLookup[model_name];

  if (!RenderComponent) {
    return <UnknownRenderer model={props.model} />;
  }

  return <RenderComponent {...props} />;
}

export function RenderRemoteInstance({
  model,
  modelUrl,
  modelRenderer,
  pk
}: Readonly<RemoteInstanceProps>): ReactNode {
  const api = useApi();

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['model', model, pk],
    queryFn: async () => {
      const url = modelUrl
        ? apiUrl(modelUrl, pk)
        : apiUrl(ModelInformationDict[model].api_endpoint, pk);

      return api.get(url).then((response) => response.data);
    }
  });

  if (isLoading || isFetching) {
    return <Skeleton />;
  }

  if (!data) {
    return (
      <Text>
        {model}: {pk}
      </Text>
    );
  }

  if (!!modelRenderer) {
    return modelRenderer({ instance: data });
  }

  return <RenderInstance model={model} instance={data} />;
}

export function UnknownRenderer({
  model
}: Readonly<{
  model: ModelType | undefined;
}>): ReactNode {
  const model_name = model ? model.toString() : 'undefined';
  return <Alert color='red' title={t`Unknown model: ${model_name}`} />;
}
