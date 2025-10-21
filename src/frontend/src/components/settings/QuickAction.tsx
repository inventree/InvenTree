import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import { Carousel } from '@mantine/carousel';
import {
  Button,
  Divider,
  Flex,
  Group,
  Paper,
  Stack,
  Text,
  Title
} from '@mantine/core';
import { IconHome } from '@tabler/icons-react';

import { ActionButton } from '@lib/index';

interface ActionItem {
  id: string;
  title: string;
  description: string;
  action: () => void;
}

function ActionCarousel({ items }: { items: ActionItem[] }) {
  const slides = items.map((image) => (
    <Carousel.Slide key={image.id}>
      <Paper shadow='xs' p='sm' withBorder>
        <Group>
          <Stack>
            <Text>
              <strong>{image.title}</strong>
              <br />
              {image.description}
            </Text>
          </Stack>
          <Button size='sm' variant='light' onClick={image.action}>
            <Trans>Act</Trans>
          </Button>
        </Group>
      </Paper>
    </Carousel.Slide>
  ));

  return (
    <Carousel
      height={80}
      slideSize='40%'
      slideGap='md'
      controlsOffset='xs'
      controlSize={28}
      emblaOptions={{ align: 'start', dragFree: true }}
    >
      {slides}
    </Carousel>
  );
}

export const QuickAction = ({
  navigate,
  ml = 'sm'
}: {
  navigate?: any;
  ml?: string;
}) => {
  const items = [
    {
      id: '1',
      title: 'Add a new group',
      description: 'Create a new group to manage your users',
      action: () => console.log('Add a new group')
    },
    {
      id: '2',
      title: 'Add a new user',
      description: 'Create a new user to manage your groups',
      action: () => console.log('Add a new user')
    },
    {
      id: '3',
      title: 'Add a new role',
      description: 'Create a new role to manage your permissions',
      action: () => console.log('Add a new role')
    }
  ];
  return (
    <Stack gap={'xs'} ml={ml}>
      <Title order={5}>
        <Trans>Quick Actions</Trans>
      </Title>
      <Flex align={'flex-end'}>
        {navigate ? (
          <>
            <ActionButton
              icon={<IconHome />}
              color='blue'
              size='lg'
              radius='sm'
              variant='filled'
              tooltip={t`Go to Home`}
              onClick={() => navigate('home')}
            />
            <Divider orientation='vertical' mx='md' />
          </>
        ) : null}
        <ActionCarousel items={items} />
      </Flex>
    </Stack>
  );
};
