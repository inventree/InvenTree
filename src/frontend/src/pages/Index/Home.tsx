import { Trans } from '@lingui/macro';
import { Title } from '@mantine/core';
import { lazy } from 'react';

import {
  LayoutItemType,
  WidgetLayout
} from '../../components/widgets/WidgetLayout';
import { LoadingItem } from '../../functions/loading';
import { useUserState } from '../../states/UserState';

const vals: LayoutItemType[] = [
  {
    i: 1,
    val: (
      <LoadingItem
        item={lazy(() => import('../../components/widgets/GetStartedWidget'))}
      />
    ),
    w: 12,
    h: 6,
    x: 0,
    y: 0,
    minH: 6
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
  }
];

export default function Home() {
  const [username] = useUserState((state) => [state.username()]);
  return (
    <>
      <Title order={1}>
        <Trans>Welcome to your Dashboard{username && `, ${username}`}</Trans>
      </Title>
      <WidgetLayout items={vals} />
    </>
  );
}
