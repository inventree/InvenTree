import { Trans } from '@lingui/macro';
import { Group, Title } from '@mantine/core';
import { lazy } from 'react';

import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';
import {
  LayoutItemType,
  WidgetLayout
} from '../../components/widgets/WidgetLayout';
import { LoadingItem } from '../../functions/loading';
import { useApiState } from '../../states/ApiState';

const vals: LayoutItemType[] = [
  {
    i: 1,
    val: (
      <LoadingItem
        item={lazy(() => import('../../components/widgets/GetStartedWidget'))}
      />
    ),
    w: 12,
    h: 7,
    x: 0,
    y: 0,
    minH: 7
  },
  {
    i: 2,
    val: (
      <LoadingItem
        item={lazy(() => import('../../components/widgets/DisplayWidget'))}
      />
    ),
    w: 3,
    h: 3,
    x: 0,
    y: 7,
    minH: 3
  },
  {
    i: 3,
    val: (
      <LoadingItem
        item={lazy(() => import('../../components/widgets/SizeDemoWidget'))}
      />
    ),
    w: 3,
    h: 4,
    x: 3,
    y: 7
  },
  {
    i: 4,
    val: (
      <LoadingItem
        item={lazy(() => import('../../components/widgets/FeedbackWidget'))}
      />
    ),
    w: 4,
    h: 6,
    x: 0,
    y: 9
  },
  { i: 5, val: 'E', w: 2, h: 3, x: 6, y: 7 }
];

export default function Home() {
  const [username] = useApiState((state) => [state.user?.name]);
  return (
    <>
      <Group>
        <StylishText>
          <Trans>Home</Trans>
        </StylishText>
        <PlaceholderPill />
      </Group>
      <Title order={3}>
        <Trans>Welcome to your Dashboard{username && `, ${username}`}</Trans>
      </Title>
      <WidgetLayout items={vals} />
    </>
  );
}
