import { Trans } from '@lingui/macro';
import { Group } from '@mantine/core';
import { Button } from '@mantine/core';
import { useState } from 'react';

import { ApiForm, ApiFormFieldType } from '../../components/forms/ApiForm';
import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';

export default function Home() {
  const [formOpened, setFormOpened] = useState(false);

  const fields: ApiFormFieldType[] = [
    {
      name: 'name'
    },
    {
      name: 'description'
    },
    {
      name: 'keywords'
    },
    {
      name: 'category'
    },
    {
      name: 'assembly'
    },
    {
      name: 'trackable'
    },
    {
      name: 'virtual'
    }
  ];

  return (
    <>
      <Group>
        <StylishText>
          <Trans>Home</Trans>
        </StylishText>
        <PlaceholderPill />
      </Group>
      <ApiForm
        name="part-edit"
        url="/part/1/"
        fields={fields}
        method="PUT"
        title="Edit Part"
        opened={formOpened}
        onClose={() => setFormOpened(false)}
      />
      <Button
        onClick={() => setFormOpened(true)}
        variant="outline"
        color="blue"
      >
        Open Form
      </Button>
    </>
  );
}
