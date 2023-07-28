import { Trans } from '@lingui/macro';
import {
  Alert,
  Grid,
  Group,
  Header,
  SimpleGrid,
  Space,
  Stack,
  Text
} from '@mantine/core';
import { Button } from '@mantine/core';
import { modals, openModal } from '@mantine/modals';
import {
  IconAlertCircle,
  IconBuilding,
  IconGlobe,
  IconKey,
  IconLink,
  IconMail,
  IconSitemap,
  IconUser,
  IconVersions,
  IconWorld
} from '@tabler/icons-react';
import { title } from 'process';
import { useState } from 'react';

import { ApiForm } from '../../components/forms/ApiForm';
import { CreateApiForm } from '../../components/forms/CreateApiForm';
import { DeleteApiForm } from '../../components/forms/DeleteApiForm';
import { EditApiForm } from '../../components/forms/EditApiForm';
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
                    hidden: true
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
