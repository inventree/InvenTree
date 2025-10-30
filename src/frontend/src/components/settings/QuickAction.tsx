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
  Text
} from '@mantine/core';
import { IconHome } from '@tabler/icons-react';

import { ActionButton, ApiEndpoints } from '@lib/index';
import {
  projectCodeFields,
  useCustomStateFields
} from '../../forms/CommonForms';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { groupFields } from '../../tables/settings/GroupTable';
import { userFields } from '../../tables/settings/UserTable';
import { StylishText } from '../items/StylishText';

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
      withIndicators
      slideGap='md'
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
  const newUser = useCreateApiFormModal(userFields());
  const newGroup = useCreateApiFormModal(groupFields());
  const newProjectCode = useCreateApiFormModal({
    url: ApiEndpoints.project_code_list,
    title: t`Add Project Code`,
    fields: projectCodeFields()
  });
  const newCustomState = useCreateApiFormModal({
    url: ApiEndpoints.custom_state_list,
    title: t`Add State`,
    fields: useCustomStateFields()
  });

  const items = [
    {
      id: '1',
      title: 'Add a new group',
      description: 'Create a new group to manage your users',
      action: () => newGroup.open()
    },
    {
      id: '2',
      title: 'Add a new user',
      description: 'Create a new user to manage your groups',
      action: () => newUser.open()
    },
    {
      id: '3',
      title: 'Add a new project code',
      description: 'Create a new project code to organize your items',
      action: () => newProjectCode.open()
    },
    {
      id: '4',
      title: 'Add a new custom state',
      description: 'Create a new custom state for your workflow',
      action: () => newCustomState.open()
    }
  ];
  return (
    <Stack gap={'xs'} ml={ml}>
      <StylishText size='lg'>
        <Trans>Quick Actions</Trans>
      </StylishText>
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
      {newUser.modal}
      {newGroup.modal}
      {newProjectCode.modal}
      {newCustomState.modal}
    </Stack>
  );
};
