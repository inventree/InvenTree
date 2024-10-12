import { t } from '@lingui/macro';
import {
  Card,
  Divider,
  Group,
  Paper,
  Skeleton,
  Stack,
  Text
} from '@mantine/core';
import { useQuery } from '@tanstack/react-query';

import { api } from '../../../App';
import { ModelType } from '../../../enums/ModelType';
import { apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { Boundary } from '../../Boundary';
import { StylishText } from '../../items/StylishText';
import { ModelInformationDict } from '../../render/ModelType';
import DashboardWidget, { DashboardWidgetProps } from '../DashboardWidget';
import QueryCountWidget from './QueryCountWidget';

function OrderSlide({ modelType }: { modelType: ModelType }) {
  const modelProperties = ModelInformationDict[modelType];

  const openOrders = useQuery({
    queryKey: ['dashboard-open-orders', modelProperties.api_endpoint],
    queryFn: () => {
      return api
        .get(apiUrl(modelProperties.api_endpoint), {
          params: {
            outstanding: true,
            limit: 1
          }
        })
        .then((res) => res.data);
    }
  });

  return (
    <Card withBorder p="sm">
      <Group gap="xs" wrap="nowrap">
        <StylishText size="md">{modelProperties.label_multiple()}</StylishText>
        {openOrders.isFetching ? (
          <Skeleton width={50} height={50} />
        ) : (
          <Text>{openOrders.data?.count ?? '-'}</Text>
        )}
      </Group>
    </Card>
  );
}

/**
 * A dashboard widget for displaying a quick summary of all open orders
 */
export default function OrdersOverviewWidget() {
  const user = useUserState();

  const widgets: DashboardWidgetProps[] = [
    QueryCountWidget({
      modelType: ModelType.build,
      title: t`Outstanding Build Orders`,
      params: { outstanding: true }
    }),
    QueryCountWidget({
      modelType: ModelType.purchaseorder,
      title: t`Outstanding Purchase Orders`,
      params: { outstanding: true }
    }),
    QueryCountWidget({
      modelType: ModelType.build,
      title: t`Overdue Build Orders`,
      params: { overdue: true }
    })
  ];

  return (
    <Boundary label="OrdersOverviewWidget">
      <Paper shadow="xs" p="sm">
        <Stack gap="xs">
          <StylishText size="xl">{t`Open Orders`}</StylishText>
          <Divider />
          <Group gap="xs">
            {user.hasViewPermission(ModelType.build) && (
              <OrderSlide modelType={ModelType.build} />
            )}
            {user.hasViewPermission(ModelType.purchaseorder) && (
              <OrderSlide modelType={ModelType.purchaseorder} />
            )}
            {user.hasViewPermission(ModelType.salesorder) && (
              <OrderSlide modelType={ModelType.salesorder} />
            )}
            {user.hasViewPermission(ModelType.returnorder) && (
              <OrderSlide modelType={ModelType.returnorder} />
            )}
          </Group>
          {widgets.map((widget, index) => (
            <DashboardWidget key={index} {...widget} />
          ))}
        </Stack>
      </Paper>
    </Boundary>
  );
}
