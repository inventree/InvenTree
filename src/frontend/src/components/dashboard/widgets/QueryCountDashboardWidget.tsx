import { ActionIcon, Group, Loader } from '@mantine/core';
import { IconExternalLink } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { type ReactNode, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

import { InvenTreeIcon, type InvenTreeIconType } from '@lib/components';
import { StylishText } from '@lib/components';
import type { ModelType } from '@lib/core';
import { ModelInformationDict } from '@lib/core';
import { apiUrl } from '@lib/functions';
import { navigateToLink } from '@lib/functions';
import { useApi } from '@lib/hooks/UseApi';
import { useUserState } from '../../../../lib/states/UserState';
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
  icon?: InvenTreeIconType;
  params: any;
}>): ReactNode {
  const api = useApi();
  const user = useUserState();
  const navigate = useNavigate();

  const modelProperties = ModelInformationDict[modelType];

  const query = useQuery({
    queryKey: ['dashboard-query-count', modelType, params],
    enabled: user.hasViewPermission(modelType),
    refetchOnMount: true,
    queryFn: () => {
      return api
        .get(apiUrl(modelProperties.api_endpoint), {
          params: {
            ...params,
            limit: 1
          }
        })
        .then((res) => res.data)
        .catch(() => {});
    }
  });

  const onFollowLink = useCallback(
    (event: any) => {
      if (modelProperties.url_overview) {
        let url = modelProperties.url_overview;

        if (params) {
          url += '?';
          for (const key in params) {
            url += `${key}=${params[key]}&`;
          }
        }

        navigateToLink(url, navigate, event);
      }
    },
    [modelProperties, params]
  );

  return (
    <Group
      gap='xs'
      wrap='nowrap'
      justify='space-between'
      align='center'
      style={{ height: '100%' }}
    >
      <Group gap='xs'>
        <InvenTreeIcon icon={icon ?? modelProperties.icon} />
        <StylishText size='md'>{title}</StylishText>
      </Group>
      <Group gap='xs' wrap='nowrap' justify='space-apart'>
        <Group gap='xs' wrap='nowrap' justify='right'>
          {query.isFetching ? (
            <Loader size='sm' />
          ) : (
            <StylishText size='md'>{query.data?.count ?? '-'}</StylishText>
          )}
          {modelProperties?.url_overview && (
            <ActionIcon size='sm' variant='transparent' onClick={onFollowLink}>
              <IconExternalLink />
            </ActionIcon>
          )}
        </Group>
      </Group>
    </Group>
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
    minWidth: 2,
    minHeight: 1,
    render: () => (
      <QueryCountWidget modelType={modelType} title={title} params={params} />
    )
  };
}
