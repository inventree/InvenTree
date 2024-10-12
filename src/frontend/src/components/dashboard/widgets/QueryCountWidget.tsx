import { Card, Group, Skeleton, Text } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { useCallback } from 'react';

import { api } from '../../../App';
import { ModelType } from '../../../enums/ModelType';
import { identifierString } from '../../../functions/conversion';
import { apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { StylishText } from '../../items/StylishText';
import { ModelInformationDict } from '../../render/ModelType';
import { DashboardWidgetProps } from '../DashboardWidget';

/**
 * A simple dashboard widget for displaying the number of results for a particular query
 */
export default function QueryCountWidget({
  modelType,
  title,
  params
}: {
  modelType: ModelType;
  title: string;
  params: any;
}): DashboardWidgetProps {
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

  const renderFunc = useCallback(() => {
    return (
      <Card withBorder p="sm">
        <Group gap="xs" wrap="nowrap">
          <StylishText size="md">
            {modelProperties.label_multiple()}
          </StylishText>
          {query.isFetching ? (
            <Skeleton width={50} height={50} />
          ) : (
            <Text>{query.data?.count ?? '-'}</Text>
          )}
        </Group>
      </Card>
    );
  }, [query.isFetching, query.data, title]);

  return {
    title: title,
    label: `count-${identifierString(title)}`,
    width: 3,
    height: 1,
    visible: () => user.hasViewPermission(modelType),
    render: renderFunc
  };
}
