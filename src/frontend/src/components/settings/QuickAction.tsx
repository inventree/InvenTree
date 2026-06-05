import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import { Button, Group, Paper, SimpleGrid, Stack, Text } from '@mantine/core';
import {
  IconBrandGithub,
  IconListCheck,
  IconUserPlus,
  IconUsersGroup,
  type ReactNode
} from '@tabler/icons-react';

import { ApiEndpoints } from '@lib/index';
import {
  projectCodeFields,
  useCustomStateFields
} from '../../forms/CommonForms';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { groupFields } from '../../tables/settings/GroupTable';
import { userFields } from '../../tables/settings/UserTable';

interface ActionItem {
  id: string;
  title: string;
  description: string;
  icon?: ReactNode;
  buttonText?: string;
  action: () => void;
}

function ActionGrid({ items }: { items: ActionItem[] }) {
  const slides = items.map((image) => (
    <Paper shadow='xs' p='sm' withBorder>
      <Group justify='space-between' wrap='nowrap'>
        <Stack>
          <Text>
            <strong>{image.title}</strong>
            <br />
            {image.description}
          </Text>
        </Stack>
        <Button
          size='sm'
          variant='light'
          onClick={image.action}
          leftSection={image.icon}
        >
          {image.buttonText ?? <Trans>Act</Trans>}
        </Button>
      </Group>
    </Paper>
  ));

  return (
    <SimpleGrid
      cols={{
        base: 1,
        '600px': 2,
        '1200px': 3
      }}
      type='container'
      spacing='sm'
    >
      {slides}
    </SimpleGrid>
  );
}

export const QuickAction = () => {
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
      id: '0',
      title: t`Open an Issue`,
      description: t`Report a bug or request a feature on GitHub`,
      icon: <IconBrandGithub />,
      buttonText: t`Open Issue`,
      action: () =>
        window.open(
          'https://github.com/inventree/inventree/issues/new',
          '_blank'
        )
    },
    {
      id: '1',
      title: t`Add New Group`,
      description: t`Create a new group to manage your users`,
      icon: <IconUsersGroup />,
      buttonText: t`New Group`,
      action: () => newGroup.open()
    },
    {
      id: '2',
      title: t`Add New User`,
      description: t`Create a new user to manage your groups`,
      icon: <IconUserPlus />,
      buttonText: t`New User`,
      action: () => newUser.open()
    },
    {
      id: '3',
      title: t`Add Project Code`,
      description: t`Create a new project code to organize your items`,
      icon: <IconListCheck />,
      buttonText: t`Add Code`,
      action: () => newProjectCode.open()
    },
    {
      id: '4',
      title: t`Add Custom State`,
      description: t`Create a new custom state for your workflow`,
      icon: <IconListCheck />,
      buttonText: t`Add State`,
      action: () => newCustomState.open()
    }
  ];

  return (
    <Stack gap={'xs'} ml={'sm'}>
      <ActionGrid items={items} />
      {newUser.modal}
      {newGroup.modal}
      {newProjectCode.modal}
      {newCustomState.modal}
    </Stack>
  );
};
