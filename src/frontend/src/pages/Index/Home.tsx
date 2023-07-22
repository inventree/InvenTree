import { Trans } from '@lingui/macro';
import { Button, Group, Modal, Stack } from '@mantine/core';
import { useState } from 'react';

import { GenericForm } from '../../components/forms/GenericForm';
import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';

export default function Home() {
  let [modalOpen, setModalOpen] = useState(false);

  return (
    <>
      <Stack>
        <Group>
          <StylishText>
            <Trans>Home</Trans>
          </StylishText>
          <PlaceholderPill />
        </Group>
        <Button
          onClick={() => {
            setModalOpen(true);
          }}
        >
          Open Modal Form
        </Button>
        <Modal
          opened={modalOpen}
          title="my modal form"
          onClose={() => {
            setModalOpen(false);
          }}
        >
          <GenericForm
            fields={[
              {
                name: 'name',
                label: 'Name',
                value: '',
                type: 'text',
                required: true,
                placeholder: 'Enter your name'
              },
              {
                name: 'email',
                label: 'Email',
                value: '',
                type: 'email',
                required: true
              },
              {
                name: 'age',
                label: 'Age',
                value: '',
                type: 'number'
              }
            ]}
          />
        </Modal>
      </Stack>
    </>
  );
}
