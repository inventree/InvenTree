import { ActionIcon, Box, Group, RollingNumber, Tooltip } from '@mantine/core';
import { IconExclamationCircle } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { type ReactNode, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { StylishText } from '@lib/components/StylishText';
import { ModelInformationDict } from '@lib/enums/ModelInformation';
import type { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { navigateToLink } from '@lib/functions/Navigation';
import type { InvenTreeIconType } from '@lib/types/Icons';
import { useDocumentVisibility } from '@mantine/hooks';
import { useApi } from '../../../contexts/ApiContext';
import { InvenTreeIcon } from '../../../functions/icons';
import { useUserState } from '../../../states/UserState';
import type { DashboardWidgetProps } from '../DashboardWidget';

/**
 * A simple dashboard widget for displaying the number of results for a particular query
 */
function QueryCountWidget({
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
  const api = useApi();
  const user = useUserState();
  const navigate = useNavigate();
  const visibility = useDocumentVisibility();

  const modelProperties = ModelInformationDict[modelType];

  const query = useQuery({
    queryKey: ['dashboard-query-count', modelType, params, visibility],
    enabled: user.hasViewPermission(modelType) && visibility === 'visible',
    refetchOnWindowFocus: true,
    refetchOnMount: true,
    refetchInterval: 10 * 60 * 1000, // 10 minute refetch interval
    staleTime: 5 * 60 * 1000, // 5 minute stale time
    queryFn: () => {
      if (visibility !== 'visible') {
        return null;
      }

      return api
        .get(apiUrl(modelProperties.api_endpoint), {
          params: {
            ...params,
            limit: 1
          }
        })
        .then((res) => {
          return res.data?.count ?? 0;
        });
    }
  });

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

  const result: ReactNode = useMemo(() => {
    if (query.isError) {
      return (
        <ActionIcon color='red' variant='transparent' size='lg'>
          <IconExclamationCircle />
        </ActionIcon>
      );
    } else {
      return (
        <RollingNumber value={query.isFetching ? 0 : query.data} fz='20px' />
      );
    }
  }, [query.isFetching, query.isError, query.data]);

  return (
    <Box
      onClick={onFollowLink}
      role='button'
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          onFollowLink(e);
        }
      }}
      style={{
        height: '100%',
        width: '100%',
        cursor: 'pointer',
        userSelect: 'none'
      }}
    >
      <Group
        gap='xs'
        wrap='nowrap'
        justify='space-between'
        align='center'
        style={{ height: '100%', width: '100%' }}
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
        <Group gap='xs' wrap='nowrap' justify='flex-end' style={{ flexShrink: 0 }}>
          {result}
        </Group>
      </Group>
    </Box>
  );
}

/**
 * Construct a dashboard widget descriptor, which displays the number of results for a particular query
 */
export default function QueryCountDashboardWidget({
  label,
  title,
  description,
  modelType,
  icon,
  enabled = true,
  params
}: {
  label: string;
  title: string;
  description: string;
  modelType: ModelType;
  icon?: keyof InvenTreeIconType;
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
    icon: icon,
    render: () => (
      <QueryCountWidget modelType={modelType} title={title} params={params} />
    )
  };
}
