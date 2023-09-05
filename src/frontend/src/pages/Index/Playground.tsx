import { Trans } from '@lingui/macro';
import { Button } from '@mantine/core';
import { Group, Text } from '@mantine/core';
import { Accordion } from '@mantine/core';
import { ReactNode } from 'react';

import { ApiFormProps } from '../../components/forms/ApiForm';
import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';
import { openCreateApiForm, openEditApiForm } from '../../functions/forms';
import {
  partCategoryFields,
  partFields
} from '../../functions/forms/PartFields';

// Generate some example forms using the modal API forms interface
function ApiFormsPlayground() {
  const createPartForm: ApiFormProps = {
    name: 'part',
    url: '/part/',
    title: 'Create Part',
    successMessage: 'Part created successfully',
    fields: partFields({})
  };

  const editPartForm: ApiFormProps = {
    name: 'part',
    url: '/part/',
    pk: 1,
    title: 'Edit Part',
    submitText: 'Save',
    cancelText: 'Custom Cancel',
    successMessage: 'Part saved successfully',
    fields: partFields({ editing: true })
  };

  const newStockForm: ApiFormProps = {
    name: 'stock',
    url: '/stock/',
    title: 'Create Stock Item',
    successMessage: 'Stock item created successfully',
    fields: {
      part: {},
      location: {},
      quantity: {}
    }
  };

  const editCategoryForm: ApiFormProps = {
    name: 'partcategory',
    url: '/part/category/',
    pk: 2,
    title: 'Edit Category',
    fields: partCategoryFields({})
  };

  return (
    <>
      <Group>
        <Button onClick={() => openCreateApiForm(createPartForm)}>
          Create New Part
        </Button>
        <Button onClick={() => openEditApiForm(editPartForm)}>
          Edit Existing Part
        </Button>
        <Button onClick={() => openCreateApiForm(newStockForm)}>
          Create New Stock Item
        </Button>
        <Button onClick={() => openEditApiForm(editCategoryForm)}>
          Edit Category
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
      <Accordion.Item value={`accordion-playground-{title}`}>
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
