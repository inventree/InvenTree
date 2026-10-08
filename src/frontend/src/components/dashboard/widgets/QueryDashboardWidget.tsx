import { Anchor, Box, Group, Tooltip } from '@mantine/core';
import { type ReactNode, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

import { StylishText } from '@lib/components/StylishText';
import { ModelInformationDict } from '@lib/enums/ModelInformation';
import type { ModelType } from '@lib/enums/ModelType';
import { navigateToLink } from '@lib/functions/Navigation';
import type { InvenTreeIconType } from '@lib/types/Icons';
import { InvenTreeIcon } from '../../../functions/icons';
import type { DashboardWidgetProps } from '../DashboardWidget';

/**
 * A simple dashboard widget for displaying a link to a particular query
 */
function QueryWidget({
  modelType,
  title,
  icon,
  params
}: Readonly<{
  modelType: ModelType;
  title: string;
  icon?: keyof InvenTreeIconType;
  params: any;
}>): ReactNode {
  const navigate = useNavigate();
  const modelProperties = ModelInformationDict[modelType];

  const onFollowLink = useCallback(
    (event: any) => {
      if (modelProperties?.url_overview) {
        let url = modelProperties.url_overview;

        if (params && Object.keys(params).length > 0) {
          const searchParams = new URLSearchParams();
          for (const key in params) {
            searchParams.append(key, String(params[key]));
          }
          const qs = searchParams.toString();
          if (qs) {
            url += `?${qs}`;
          }
        }

        navigateToLink(url, navigate, event);
      }
    },
    [modelProperties, params, navigate]
  );

  return (
    <Anchor
      href='#'
      onClick={onFollowLink}
      underline='never'
      style={{ display: 'block', height: '100%' }}
    >
      <Group
        gap='xs'
        wrap='nowrap'
        justify='space-between'
        align='center'
        style={{ height: '100%' }}
      >
        <Group
          gap='xs'
          wrap='nowrap'
          style={{ minWidth: 0, flex: 1, overflow: 'hidden' }}
        >
          <Box
            className='widget-icon-wrapper'
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(2, 132, 199, 0.08)',
              border: '1px solid rgba(2, 132, 199, 0.12)',
              transition: 'all 0.25s ease',
              flexShrink: 0
            }}
          >
            <InvenTreeIcon icon={icon ?? modelProperties.icon} />
          </Box>
          <Tooltip label={title} position='top' withArrow disabled={title.length < 14}>
            <Box style={{ minWidth: 0, overflow: 'hidden' }}>
              <StylishText size='sm' truncate='end'>
                {title}
              </StylishText>
            </Box>
          </Tooltip>
        </Group>
      </Group>
    </Anchor>
  );
}

/**
 * Construct a dashboard widget descriptor, which displays just a link to a particular query
 */
export default function QueryDashboardWidget({
  label,
  title,
  description,
  modelType,
  enabled = true,
  params
}: {
  label: string;
  title: string;
  description: string;
  modelType: ModelType;
  enabled?: boolean;
  params: any;
}): DashboardWidgetProps {
  return {
    label: label,
    title: title,
    description: description,
    enabled: enabled,
    modelType: modelType,
    minWidth: 2,
    minHeight: 2,
    render: () => (
      <QueryWidget modelType={modelType} title={title} params={params} />
    )
  };
}
