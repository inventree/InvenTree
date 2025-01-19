import { t } from '@lingui/macro';
import { Alert, Anchor, Group, Skeleton, Space, Text } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { type ReactNode, useCallback } from 'react';

import { useApi } from '../../contexts/ApiContext';
import { ModelType } from '../../enums/ModelType';
import { navigateToLink } from '../../functions/navigation';
import { shortenString } from '../../functions/tables';
import { apiUrl } from '../../states/ApiState';
import { Thumbnail } from '../images/Thumbnail';
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
  RenderProjectCode,
  RenderSelectionList
} from './Generic';
import { ModelInformationDict } from './ModelType';
import {
  RenderPurchaseOrder,
  RenderReturnOrder,
  RenderReturnOrderLineItem,
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
import { RenderGroup, RenderOwner, RenderUser } from './User';

type EnumDictionary<T extends string | symbol | number, U> = {
  [K in T]: U;
};

export interface InstanceRenderInterface {
  instance: any;
  link?: boolean;
  navigate?: any;
  showSecondary?: boolean;
}

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
  [ModelType.builditem]: RenderBuildItem,
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
  [ModelType.error]: RenderError
};

export type RenderInstanceProps = {
  model: ModelType | undefined;
} & InstanceRenderInterface;

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
  pk
}: Readonly<{
  model: ModelType;
  pk: number;
}>): ReactNode {
  const api = useApi();

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['model', model, pk],
    queryFn: async () => {
      const url = apiUrl(ModelInformationDict[model].api_endpoint, pk);

      return api
        .get(url)
        .then((response) => response.data)
        .catch(() => null);
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

  return <RenderInstance model={model} instance={data} />;
}

/**
 * Helper function for rendering an inline model in a consistent style
 */
export function RenderInlineModel({
  primary,
  secondary,
  prefix,
  suffix,
  image,
  labels,
  url,
  navigate,
  showSecondary = true,
  tooltip
}: Readonly<{
  primary: string;
  secondary?: string;
  showSecondary?: boolean;
  prefix?: ReactNode;
  suffix?: ReactNode;
  image?: string;
  labels?: string[];
  url?: string;
  navigate?: any;
  tooltip?: string;
}>): ReactNode {
  // TODO: Handle labels

  const onClick = useCallback(
    (event: any) => {
      if (url && navigate) {
        navigateToLink(url, navigate, event);
      }
    },
    [url, navigate]
  );

  const primaryText = shortenString({
    str: primary,
    len: 50
  });

  const secondaryText = shortenString({
    str: secondary,
    len: 75
  });

  return (
    <Group gap='xs' justify='space-between' wrap='nowrap' title={tooltip}>
      <Group gap='xs' justify='left' wrap='nowrap'>
        {prefix}
        {image && <Thumbnail src={image} size={18} />}
        {url ? (
          <Anchor href='' onClick={(event: any) => onClick(event)}>
            <Text size='sm'>{primaryText}</Text>
          </Anchor>
        ) : (
          <Text size='sm'>{primaryText}</Text>
        )}
        {showSecondary && secondary && <Text size='xs'>{secondaryText}</Text>}
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
}: Readonly<{
  model: ModelType | undefined;
}>): ReactNode {
  return <Alert color='red' title={t`Unknown model: ${model}`} />;
}
