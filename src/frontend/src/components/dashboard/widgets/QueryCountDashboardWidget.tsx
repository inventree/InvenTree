import { ActionIcon, Anchor, Group, Loader } from '@mantine/core';
import { IconExclamationCircle } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { type ReactNode, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { ModelInformationDict } from '@lib/enums/ModelInformation';
import type { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { navigateToLink } from '@lib/functions/Navigation';
import type { InvenTreeIconType } from '@lib/types/Icons';
import { useDocumentVisibility } from '@mantine/hooks';
import { useApi } from '../../../contexts/ApiContext';
import { InvenTreeIcon } from '../../../functions/icons';
import { useUserState } from '../../../states/UserState';
import { StylishText } from '../../items/StylishText';
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
    refetchOnMount: true,
    refetchInterval: 10 * 60 * 1000, // 10 minute refetch interval
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
        .then((res) => res.data);
    }
  });

  const onFollowLink = useCallback(
    (event: any) => {
      if (!query.isFetched) {
        return;
      }

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
    [query.isFetched, modelProperties, params]
  );

  const result: ReactNode = useMemo(() => {
    if (query.isFetching) {
      return <Loader size='xs' />;
    } else if (query.isError) {
      return (
        <ActionIcon color='red' variant='transparent' size='lg'>
          <IconExclamationCircle />
        </ActionIcon>
      );
    } else {
      return <StylishText size='xl'>{query.data?.count ?? '-'}</StylishText>;
    }
  }, [query.isFetching, query.isError, query.data]);

  return (
    <Anchor href='#' onClick={onFollowLink}>
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
            {result}
          </Group>
        </Group>
      </Group>
    </Anchor>
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
    modelType: modelType,
    minWidth: 2,
    minHeight: 1,
    render: () => (
      <QueryCountWidget modelType={modelType} title={title} params={params} />
    )
  };
}
