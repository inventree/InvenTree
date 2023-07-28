import { Trans } from '@lingui/macro';
import { Alert, Group, SimpleGrid, Space, Text } from '@mantine/core';
import { Button } from '@mantine/core';
import { IconKey, IconSitemap } from '@tabler/icons-react';

import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';
import { openEditApiForm, openModalApiForm } from '../../functions/forms';

export default function Home() {
  return (
    <>
      <Group>
        <StylishText>
          <Trans>Home</Trans>
        </StylishText>
        <PlaceholderPill />
      </Group>

      <Space />
      <Text size="xl">Test Forms</Text>
      <SimpleGrid cols={4}>
        <Button
          variant="outline"
          color="lime"
          onClick={() =>
            openEditApiForm({
              title: 'A test dynamic form',
              props: {
                name: 'my form',
                onClose: () => {
                  // TODO: Some custom action?
                  console.log('closing modal form');
                },
                url: '/part/',
                pk: 3,
                method: 'PUT',
                title: 'a title',
                preFormContent: <Text>dynamic content before the form</Text>,
                postFormContent: () => (
                  <Alert title="alert" color="blue">
                    You can call a function too!
                  </Alert>
                ),
                fields: [
                  {
                    name: 'name'
                  },
                  {
                    name: 'category',
                    icon: <IconSitemap />
                  },
                  {
                    name: 'description'
                  },
                  {
                    name: 'keywords',
                    icon: <IconKey />
                  },
                  {
                    name: 'IPN'
                  }
                ]
              }
            })
          }
        >
          Dynamic Form
        </Button>
      </SimpleGrid>
    </>
  );
}
