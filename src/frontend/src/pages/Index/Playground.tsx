import { Trans } from '@lingui/macro';
import { Button, Card, Stack, TextInput } from '@mantine/core';
import { Group, Text } from '@mantine/core';
import { Accordion } from '@mantine/core';
import { ReactNode, useMemo, useState } from 'react';

import { OptionsApiForm } from '../../components/forms/ApiForm';
import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';
import { ModelType } from '../../components/render/ModelType';
import { StatusRenderer } from '../../components/renderers/StatusRenderer';
import {
  createPart,
  editPart,
  partCategoryFields,
  partFields
} from '../../forms/PartForms';
import { createStockItem } from '../../forms/StockForms';
import {
  OpenApiFormProps,
  openCreateApiForm,
  openEditApiForm
} from '../../functions/forms';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { ApiPaths } from '../../states/ApiState';

// Generate some example forms using the modal API forms interface
const fields = partCategoryFields({});
function ApiFormsPlayground() {
  const editCategoryForm: OpenApiFormProps = {
    url: ApiPaths.category_list,
    pk: 2,
    title: 'Edit Category',
    fields: fields
  };

  const createAttachmentForm: OpenApiFormProps = {
    url: ApiPaths.part_attachment_list,
    title: 'Create Attachment',
    successMessage: 'Attachment uploaded',
    fields: {
      part: {
        value: 1
      },
      attachment: {},
      comment: {}
    }
  };

  const partFieldsState: any = useMemo<any>(() => partFields({}), []);

  const { open, modal } = useCreateApiFormModal({
    url: ApiPaths.part_list,
    title: 'Create part',
    fields: partFieldsState
  });

  const [active, setActive] = useState(true);

  return (
    <Stack>
      <Group>
        <Button onClick={() => createPart()}>Create New Part</Button>
        <Button onClick={() => editPart({ part_id: 1 })}>Edit Part</Button>
        <Button onClick={() => createStockItem()}>Create Stock Item</Button>
        <Button onClick={() => openEditApiForm(editCategoryForm)}>
          Edit Category
        </Button>
        <Button onClick={() => openCreateApiForm(createAttachmentForm)}>
          Create Attachment
        </Button>
        <Button onClick={() => open()}>Create Part new Modal</Button>
        {modal}
      </Group>
      <Card sx={{ padding: '30px' }}>
        <OptionsApiForm
          props={{
            url: ApiPaths.part_list,
            method: 'POST',
            fields: {
              active: {
                onValueChange: ({ value }) => {
                  setActive(value);
                }
              },
              keywords: {
                disabled: active
              }
            }
          }}
          id={'this is very unique'}
        />
      </Card>
    </Stack>
  );
}

// Show some example status labels
function StatusLabelPlayground() {
  const [status, setStatus] = useState<string>('10');
  return (
    <>
      <Group>
        <Text>Stock Status</Text>
        <TextInput
          value={status}
          onChange={(event) => setStatus(event.currentTarget.value)}
        />
        <StatusRenderer type={ModelType.stockitem} status={status} />
      </Group>
    </>
  );
}

/** Construct a simple accordion group with title and content */
function PlaygroundArea({
  title,
  content
}: {
  title: string;
  content: ReactNode;
}) {
  return (
    <>
      <Accordion.Item value={`accordion-playground-${title}`}>
        <Accordion.Control>
          <Text>{title}</Text>
        </Accordion.Control>
        <Accordion.Panel>{content}</Accordion.Panel>
      </Accordion.Item>
    </>
  );
}

export default function Playground() {
  return (
    <>
      <Group>
        <StylishText>
          <Trans>Playground</Trans>
        </StylishText>
        <PlaceholderPill />
      </Group>
      <Text>
        <Trans>
          This page is a showcase for the possibilities of Platform UI.
        </Trans>
      </Text>
      <Accordion defaultValue="">
        <PlaygroundArea title="API Forms" content={<ApiFormsPlayground />} />
        <PlaygroundArea
          title="Status labels"
          content={<StatusLabelPlayground />}
        />
      </Accordion>
    </>
  );
}
