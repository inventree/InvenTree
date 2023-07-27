import { Trans } from '@lingui/macro';
import { Group } from '@mantine/core';
import { Button } from '@mantine/core';
import { useState } from 'react';

import { ApiForm, ApiFormField } from '../../components/forms/ApiForm';
import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';

export default function Home() {
  const [formOpened, setFormOpened] = useState(false);

  const fields: ApiFormField[] = [
    {
      name: 'name'
    },
    {
      name: 'description'
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
