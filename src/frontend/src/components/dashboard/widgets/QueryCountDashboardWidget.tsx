import {
  ActionIcon,
  Card,
  Group,
  Loader,
  Skeleton,
  Space,
  Stack,
  Text
} from '@mantine/core';
import { IconExternalLink } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { ReactNode, useCallback } from 'react';

import { api } from '../../../App';
import { ModelType } from '../../../enums/ModelType';
import { identifierString } from '../../../functions/conversion';
import { InvenTreeIcon } from '../../../functions/icons';
import { apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { StylishText } from '../../items/StylishText';
import { ModelInformationDict } from '../../render/ModelType';
import { DashboardWidgetProps } from '../DashboardWidget';

/**
 * A simple dashboard widget for displaying the number of results for a particular query
 */
function QueryCountWidget({
  modelType,
  title,
  params
}: {
  modelType: ModelType;
  title: string;
  params: any;
}): ReactNode {
  const user = useUserState();

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
        .then((res) => res.data);
    }
  });

  return (
    <Stack justify="middle" align="stretch">
      <Group gap="xs" wrap="nowrap">
        <InvenTreeIcon icon={modelProperties.icon} />
        <StylishText size="md">{title}</StylishText>
        <Group gap="xs" wrap="nowrap" justify="space-apart">
          {query.isFetching ? (
            <Loader size="sm" />
          ) : (
            <StylishText size="sm">{query.data?.count ?? '-'}</StylishText>
          )}
          <Space />
          <ActionIcon variant="transparent">
            <IconExternalLink />
          </ActionIcon>
        </Group>
      </Group>
    </Stack>
  );
}

/**
 * Construct a dashboard widget descriptor, which displays the number of results for a particular query
 */
export default function QueryCountDashboardWidget({
  title,
  modelType,
  params
}: {
  title: string;
  modelType: ModelType;
  params: any;
}): DashboardWidgetProps {
  return {
    label: identifierString(title),
    minWidth: 2,
    minHeight: 1,
    render: () => (
      <QueryCountWidget modelType={modelType} title={title} params={params} />
    )
  };
}
