import { ActionIcon, Group, Loader } from '@mantine/core';
import { IconExternalLink } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { type ReactNode, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

import { useApi } from '../../../contexts/ApiContext';
import type { ModelType } from '../../../enums/ModelType';
import {
  InvenTreeIcon,
  type InvenTreeIconType
} from '../../../functions/icons';
import { navigateToLink } from '../../../functions/navigation';
import { apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { StylishText } from '../../items/StylishText';
import { ModelInformationDict } from '../../render/ModelType';
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

  // TODO: Improve visual styling

  return (
    <Group gap='xs' wrap='nowrap'>
      <InvenTreeIcon icon={icon ?? modelProperties.icon} />
      <Group gap='xs' wrap='nowrap' justify='space-between'>
        <StylishText size='md'>{title}</StylishText>
        <Group gap='xs' wrap='nowrap' justify='right'>
          {query.isFetching ? (
            <Loader size='sm' />
          ) : (
            <StylishText size='sm'>{query.data?.count ?? '-'}</StylishText>
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
