import { ModelInformationDict } from '@lib/enums/ModelInformation';
import type { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import type {
  InstanceRenderInterface,
  RemoteInstanceProps,
  RenderInlineModelProps,
  RenderInstanceProps
} from '@lib/types/Rendering';
import { t } from '@lingui/core/macro';
import {
  ActionIcon,
  Alert,
  Anchor,
  Box,
  Group,
  HoverCard,
  type MantineSize,
  Paper,
  Skeleton,
  Space,
  Stack,
  Text
} from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { type ReactNode, useCallback, useMemo } from 'react';

export type { InstanceRenderInterface } from '@lib/types/Rendering';

import {
  getBaseUrl,
  getDetailUrl,
  navigateToLink
} from '@lib/functions/Navigation';
import { shortenString } from '@lib/functions/String';
import { IconLink } from '@tabler/icons-react';
import { useApi } from '../../contexts/ApiContext';
import { usePluginState } from '../../states/PluginState';
import { useUserSettingsState } from '../../states/SettingsStates';
import { Thumbnail } from '../images/Thumbnail';
import './ModelRenderShim';

/**
 * Render an instance of a database model, depending on the provided data
 */
export function RenderInstance(props: RenderInstanceProps): ReactNode {
  // Extract model information from the defined model type
  const modelInfo = useMemo(() => {
    if (!props.model) {
      return undefined;
    }

    return ModelInformationDict[
      props.model.toString().toLowerCase() as ModelType
    ];
  }, [props.model]);

  let RenderComponent:
    | ((props: Readonly<InstanceRenderInterface>) => ReactNode)
    | undefined;

  // core model renderer
  if (props.model !== undefined && props.custom_model === undefined) {
    RenderComponent = modelInfo?.render;
  }

  // custom model renderer (registered by a plugin) as a fallback to the core model renderer
  RenderComponent ??= usePluginState().getRenderer(
    props.custom_model ?? props.model ?? ''
  );

  const userSettings = useUserSettingsState();

  const showHover: boolean = useMemo(() => {
    if (!modelInfo) {
      return false;
    }

    // Override with the props.showHover attribute
    if (props.showHover !== undefined) {
      return props.showHover;
    }

    // If not specified, fall back to the user configured setting
    return userSettings.isSet('SHOW_EXTRA_MODEL_INFO');
  }, [props.showHover, modelInfo, userSettings]);

  // Extract model ID from the provided instance data, using the defined primary key field (or 'pk' as a fallback)
  const modelId = useMemo(() => {
    if (!modelInfo || !props.instance) {
      return undefined;
    }

    return props.instance[modelInfo.pk_field ?? 'pk'];
  }, [modelInfo, props.instance]);

  const detailUrl = useMemo(() => {
    if (!props.model) {
      return undefined;
    }

    return getDetailUrl(props.model, modelId, true);
  }, [props.model]);

  return (
    <HoverCard
      disabled={!showHover}
      position='top-end'
      withinPortal
      openDelay={500}
      closeDelay={100}
      zIndex={99999}
    >
      <HoverCard.Target>
        <Box>
          {!!RenderComponent ? (
            <RenderComponent {...props} />
          ) : (
            <UnknownRenderer model={props.model} />
          )}
        </Box>
      </HoverCard.Target>
      <HoverCard.Dropdown>
        <Stack gap='xs'>
          <Group justify='space-between'>
            <Text size='sm' fw='bold'>
              {modelInfo?.label()}
            </Text>
            {modelId && <Text size='xs'>{`[${t`ID`}: ${modelId}]`}</Text>}
          </Group>
          {detailUrl && (
            <Anchor
              href={detailUrl}
              target='_blank'
              onClick={(event) => {
                if (props.navigate) {
                  navigateToLink(detailUrl, props.navigate, event);
                }
              }}
            >
              <Group gap='xs' wrap='nowrap'>
                <ActionIcon variant='transparent' size='xs'>
                  <IconLink />
                </ActionIcon>
                <Text size='sm'>{t`View details`}</Text>
              </Group>
            </Anchor>
          )}
        </Stack>
      </HoverCard.Dropdown>
    </HoverCard>
  );
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
}: Readonly<RenderInlineModelProps>): ReactNode {
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
