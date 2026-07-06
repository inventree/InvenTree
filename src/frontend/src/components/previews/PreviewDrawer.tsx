import {
  ActionIcon,
  Anchor,
  Divider,
  Drawer,
  Group,
  LoadingOverlay,
  Stack,
  Tooltip
} from '@mantine/core';

import { StylishText } from '@lib/components/StylishText';
import { ModelInformationDict } from '@lib/enums/ModelInformation';
import { cancelEvent } from '@lib/functions/Events';
import {
  eventModified,
  getBaseUrl,
  getDetailUrl,
  navigateToLink
} from '@lib/functions/Navigation';
import type { ModelType } from '@lib/index';
import { t } from '@lingui/core/macro';
import { IconArrowRight } from '@tabler/icons-react';
import type React from 'react';
import { useCallback, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useInstance } from '../../hooks/UseInstance';
import { getModelInfo } from '../render/ModelType';
import { type PreviewType, getPreviewComponentForModel } from './PreviewType';
import { FallbackPreviewComponent } from './models/Fallback';

export default function PreviewDrawer({
  modelType,
  id,
  instance: providedInstance,
  filters,
  preview: providedPreview,
  targetUrl,
  opened,
  onClose
}: Readonly<{
  modelType?: ModelType;
  id?: number | string;
  instance?: any;
  filters?: Record<string, any>;
  preview?: PreviewType;
  targetUrl?: string;
  opened: boolean;
  onClose: () => void;
}>) {
  const navigate = useNavigate();

  const modelInfo = modelType ? getModelInfo(modelType) : null;
  const apiEndpoint = modelType
    ? ModelInformationDict[modelType].api_endpoint
    : undefined;

  const { instance: fetchedInstance, instanceQuery } = useInstance({
    endpoint: apiEndpoint!,
    pk: id,
    hasPrimaryKey: true,
    defaultValue: {},
    params: filters,
    disabled: !!providedInstance || !modelType || !id
  });

  const instance = useMemo(() => {
    return providedInstance ?? fetchedInstance;
  }, [providedInstance, fetchedInstance]);

  const previewComponent: PreviewType | null = useMemo(() => {
    if (providedPreview) return providedPreview;
    if (!modelType || !modelInfo || id == null) return null;

    const component: PreviewType | null = getPreviewComponentForModel({
      modelType,
      instance,
      modelId: typeof id === 'string' ? Number(id) : id
    });

    if (component == null) {
      return FallbackPreviewComponent({
        modelInfo,
        modelType,
        modelId: id,
        instance
      });
    }

    return component;
  }, [providedPreview, modelType, id, instance]);

  useEffect(() => {
    if (!opened) return;
    const handler = (event: MouseEvent) => {
      const anchor = (event.target as HTMLElement).closest('a');
      if (anchor && !eventModified(event as any)) {
        if (anchor.origin === window.location.origin) {
          // Same-origin: prevent browser navigation and route internally
          const href = anchor.pathname + anchor.search + anchor.hash;
          cancelEvent(event);
          onClose();
          navigateToLink(href, navigate, event as any);
        } else {
          // External link: let browser open it, just close the drawer
          onClose();
        }
      }
    };
    document.addEventListener('click', handler, true);
    return () => document.removeEventListener('click', handler, true);
  }, [onClose, opened]);

  const primaryUrl = useMemo(() => {
    if (targetUrl) return targetUrl;
    if (modelType && id) return getDetailUrl(modelType, id);
    return undefined;
  }, [targetUrl, modelType, id]);

  const primaryHref = useMemo(() => {
    if (!primaryUrl) return undefined;
    const base = `/${getBaseUrl()}`;
    return primaryUrl.startsWith(base) ? primaryUrl : `${base}${primaryUrl}`;
  }, [primaryUrl]);

  const clickTitle = useCallback(
    (
      event: Parameters<
        React.AnchorHTMLAttributes<HTMLAnchorElement>['onClick'] & {}
      >[0]
    ) => {
      if (!primaryUrl) return;

      if (!eventModified(event as any)) {
        onClose();
      }
      navigateToLink(primaryUrl, navigate, event as any);
    },
    [primaryUrl, navigate]
  );

  return (
    <Drawer
      position='right'
      size='xl'
      title={
        previewComponent ? (
          primaryHref ? (
            <Anchor href={primaryHref} onClick={(e) => clickTitle(e)}>
              <Group aria-label={`details-${modelType}-${id}`} gap='xs'>
                <Tooltip label={t`View Details`} position='left'>
                  <ActionIcon variant='transparent' size='lg'>
                    <IconArrowRight />
                  </ActionIcon>
                </Tooltip>
                <StylishText size='lg'>{previewComponent.title}</StylishText>
              </Group>
            </Anchor>
          ) : (
            <StylishText size='lg'>{previewComponent.title}</StylishText>
          )
        ) : null
      }
      opened={opened}
      onClose={onClose}
      withCloseButton
      transitionProps={{
        transition: 'slide-left',
        duration: 300,
        timingFunction: 'ease'
      }}
    >
      <Stack gap='xs'>
        {previewComponent && (
          <>
            <Divider />
            <LoadingOverlay visible={instanceQuery.isFetching} />
            {previewComponent.preview}
          </>
        )}
      </Stack>
    </Drawer>
  );
}
