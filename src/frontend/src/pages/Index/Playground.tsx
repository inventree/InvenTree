import { Trans } from '@lingui/macro';
import { Button, Card, Stack, TextInput } from '@mantine/core';
import { Group, Text } from '@mantine/core';
import { Accordion } from '@mantine/core';
import { ReactNode, useMemo, useState } from 'react';

import { OptionsApiForm } from '../../components/forms/ApiForm';
import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';
import { StatusRenderer } from '../../components/render/StatusRenderer';
import { ApiPaths } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import {
  createPart,
  editPart,
  partCategoryFields,
  partFields
} from '../../forms/PartForms';
import { useCreateStockItem } from '../../forms/StockForms';
import {
  OpenApiFormProps,
  openCreateApiForm,
  openEditApiForm
} from '../../functions/forms';
import { useCreateApiFormModal } from '../../hooks/UseForm';

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
  const [active, setActive] = useState(true);
  const [name, setName] = useState('Hello');

  const partFieldsState: any = useMemo<any>(() => {
    const fields = partFields({});
    fields.name = {
      ...fields.name,
      value: name,
      onValueChange: setName
    };
    fields.active = {
      ...fields.active,
      value: active,
      onValueChange: setActive
    };
    fields.responsible = {
      ...fields.responsible,
      disabled: !active
    };
    return fields;
  }, [name, active]);

  const { modal: createPartModal, open: openCreatePart } =
    useCreateApiFormModal({
      url: ApiPaths.part_list,
      title: 'Create part',
      fields: partFieldsState,
      initialData: {
        is_template: true,
        virtual: true,
        minimum_stock: 10,
        keywords: 'apple, banana, carrottt'
      },
      preFormContent: (
        <Button onClick={() => setName('Hello world')}>
          Set name="Hello world"
        </Button>
      )
    });

  const { modal: createStockItemModal, open: openCreateStockItem } =
    useCreateStockItem();

  return (
    <Stack>
      <Group>
        <Button onClick={() => createPart()}>Create New Part</Button>
        <Button onClick={() => editPart({ part_id: 1 })}>Edit Part</Button>

        <Button onClick={() => openCreateStockItem()}>Create Stock Item</Button>
        {createStockItemModal}

        <Button onClick={() => openEditApiForm(editCategoryForm)}>
          Edit Category
        </Button>

        <Button onClick={() => openCreateApiForm(createAttachmentForm)}>
          Create Attachment
        </Button>

        <Button onClick={() => openCreatePart()}>Create Part new Modal</Button>
        {createPartModal}
      </Group>
      <Card sx={{ padding: '30px' }}>
        <OptionsApiForm
          props={{
            url: ApiPaths.part_list,
            method: 'POST',
            fields: {
              active: {
                value: active,
                onValueChange: setActive
              },
              keywords: {
                disabled: !active,
                value: 'default,test,placeholder'
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
