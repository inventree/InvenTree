import { t } from '@lingui/core/macro';
import {
  Alert,
  Anchor,
  Group,
  type MantineSize,
  Paper,
  Skeleton,
  Space,
  Text
} from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { type ReactNode, useCallback } from 'react';

import { ModelInformationDict } from '@lib/enums/ModelInformation';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { getBaseUrl, navigateToLink } from '@lib/functions/Navigation';
import type {
  ModelRendererDict,
  RenderInstanceProps
} from '@lib/types/Rendering';
export type { InstanceRenderInterface } from '@lib/types/Rendering';
import { useApi } from '../../contexts/ApiContext';
import { shortenString } from '../../functions/tables';
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
  RenderParameter,
  RenderParameterTemplate,
  RenderProjectCode,
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
  primary: ReactNode;
  secondary?: ReactNode;
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

  if (typeof primary === 'string') {
    primary = shortenString({
      str: primary,
      len: 50
    });

    primary = <Text size='sm'>{primary}</Text>;
  }

  if (typeof secondary === 'string') {
    secondary = shortenString({
      str: secondary,
      len: 75
    });

    if (secondary.toString()?.length > 0) {
      secondary = <InlineSecondaryBadge text={secondary.toString()} />;
    }
  }

  if (typeof suffix === 'string') {
    suffix = <Text size='xs'>{suffix}</Text>;
  }

  return (
    <Group gap='xs' justify='space-between' title={tooltip}>
      <Group gap='xs' justify='left'>
        {prefix}
        {image && <Thumbnail src={image} size={18} />}
        {url ? (
          <Anchor
            href={`/${getBaseUrl()}${url}`}
            onClick={(event: any) => onClick(event)}
          >
            {primary}
          </Anchor>
        ) : (
          primary
        )}
        {showSecondary && secondary && secondary}
      </Group>
      {suffix && (
        <>
          <Space />
          {suffix}
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
  const model_name = model ? model.toString() : 'undefined';
  return <Alert color='red' title={t`Unknown model: ${model_name}`} />;
}

/**
 * Render a "badge like" component with a text label
 */
export function InlineSecondaryBadge({
  text,
  title,
  size = 'xs'
}: {
  text: string;
  title?: string;
  size?: MantineSize;
}): ReactNode {
  return (
    <Paper p={2} withBorder style={{ backgroundColor: 'transparent' }}>
      <Group gap='xs' wrap='nowrap'>
        {title && (
          <Text size={size} title={title}>
            {title}:
          </Text>
        )}
        <Text size={size ?? 'xs'}>{text}</Text>
      </Group>
    </Paper>
  );
}
