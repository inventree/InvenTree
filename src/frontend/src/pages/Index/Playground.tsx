import { Trans } from '@lingui/macro';
import { Button } from '@mantine/core';
import { Group, Text } from '@mantine/core';
import { Accordion } from '@mantine/core';
import { ReactNode } from 'react';

import { ApiFormProps } from '../../components/forms/ApiForm';
import { ApiFormChangeCallback } from '../../components/forms/fields/ApiFormField';
import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';
import { openCreateApiForm, openEditApiForm } from '../../functions/forms';
import {
  createPart,
  editPart,
  partCategoryFields
} from '../../functions/forms/PartForms';
import { createStockItem } from '../../functions/forms/StockForms';
import { ApiPaths } from '../../states/ApiState';

// Generate some example forms using the modal API forms interface
function ApiFormsPlayground() {
  let fields = partCategoryFields({});

  const editCategoryForm: ApiFormProps = {
    name: 'partcategory',
    url: ApiPaths.category_list,
    pk: 2,
    title: 'Edit Category',
    fields: fields
  };

  const createAttachmentForm: ApiFormProps = {
    name: 'createattachment',
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

  return (
    <>
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
        <PlaygroundArea
          title="API Forms"
          content={<ApiFormsPlayground />}
        ></PlaygroundArea>
      </Accordion>
    </>
  );
}
