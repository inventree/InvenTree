import { Trans } from '@lingui/macro';
import {
  Accordion,
  Button,
  Card,
  Group,
  Stack,
  Text,
  TextInput
} from '@mantine/core';
import { spotlight } from '@mantine/spotlight';
import { IconAlien } from '@tabler/icons-react';
import { ReactNode, useCallback, useMemo, useState } from 'react';

import { OptionsApiForm } from '../../components/forms/ApiForm';
import ImporterDrawer from '../../components/importer/ImporterDrawer';
import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';
import { StatusRenderer } from '../../components/render/StatusRenderer';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { dataImporterSessionFields } from '../../forms/ImporterForms';
import { partCategoryFields, usePartFields } from '../../forms/PartForms';
import { useCreateStockItem } from '../../forms/StockForms';
import {
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';

// Generate some example forms using the modal API forms interface
const fields = partCategoryFields({});

function ApiFormsPlayground() {
  const editCategory = useEditApiFormModal({
    url: ApiEndpoints.category_list,
    pk: 2,
    title: 'Edit Category',
    fields: fields
  });

  const createPartFields = usePartFields({ create: true });
  const editPartFields = usePartFields({ create: false });

  const newPart = useCreateApiFormModal({
    url: ApiEndpoints.part_list,
    title: 'Create Part',
    fields: createPartFields,
    initialData: {
      description: 'A part created via the API'
    }
  });

  const editPart = useEditApiFormModal({
    url: ApiEndpoints.part_list,
    pk: 1,
    title: 'Edit Part',
    fields: editPartFields
  });

  const newAttachment = useCreateApiFormModal({
    url: ApiEndpoints.part_attachment_list,
    title: 'Create Attachment',
    fields: {
      part: {},
      attachment: {},
      comment: {}
    },
    initialData: {
      part: 1
    },
    successMessage: 'Attachment uploaded'
  });

  const [active, setActive] = useState(true);
  const [name, setName] = useState('Hello');

  const partFieldsState: any = useMemo<any>(() => {
    const fields = editPartFields;
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
      url: ApiEndpoints.part_list,
      title: 'Create part',
      fields: partFieldsState,
      initialData: {
        is_template: true,
        virtual: true,
        minimum_stock: 10,
        description: 'An example part description',
        keywords: 'apple, banana, carrottt',
        'initial_supplier.sku': 'SKU-123'
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
        <Button onClick={() => newPart.open()}>Create New Part</Button>
        {newPart.modal}

        <Button onClick={() => editPart.open()}>Edit Part</Button>
        {editPart.modal}

        <Button onClick={() => openCreateStockItem()}>Create Stock Item</Button>
        {createStockItemModal}

        <Button onClick={() => editCategory.open()}>Edit Category</Button>
        {editCategory.modal}

        <Button onClick={() => newAttachment.open()}>Create Attachment</Button>
        {newAttachment.modal}

        <Button onClick={() => openCreatePart()}>Create Part new Modal</Button>
        {createPartModal}
      </Group>
      <Card sx={{ padding: '30px' }}>
        <OptionsApiForm
          props={{
            url: ApiEndpoints.part_list,
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

// Data importing
function DataImportingPlayground() {
  const [opened, setOpened] = useState<boolean>(false);

  const importSessionFields = dataImporterSessionFields();

  const [importSessionId, setImportSessionId] = useState<number>(0);

  const createNewImportSession = useCreateApiFormModal({
    url: ApiEndpoints.import_session_list,
    title: 'Create Import Session',
    fields: importSessionFields,
    initialData: {
      parent: 1,
      model: 'partcategory'
    },
    onFormSuccess: (response: any) => {
      setImportSessionId(response.pk);
      setOpened(true);
    }
  });

  const openDrawer = useCallback(() => {
    createNewImportSession.open();
  }, []);

  return (
    <>
      {createNewImportSession.modal}
      <Button onClick={() => openDrawer()}>Open Importer</Button>
      <ImporterDrawer
        sessionId={importSessionId}
        opened={opened}
        onClose={() => setOpened(false)}
      />
    </>
  );
}

// Sample for spotlight actions
function SpotlighPlayground() {
  return (
    <Button
      variant="outline"
      onClick={() => {
        spotlight.registerActions([
          {
            id: 'secret-action-1',
            title: 'Secret action',
            description: 'It was registered with a button click',
            icon: <IconAlien size="1.2rem" />,
            onTrigger: () => console.log('Secret')
          },
          {
            id: 'secret-action-2',
            title: 'Another secret action',
            description:
              'You can register multiple actions with just one command',
            icon: <IconAlien size="1.2rem" />,
            onTrigger: () => console.log('Secret')
          }
        ]);
        console.log('registed');
        spotlight.open();
      }}
    >
      Register extra actions
    </Button>
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
        <PlaygroundArea
          title="Data Import"
          content={<DataImportingPlayground />}
        />
        <PlaygroundArea
          title="Spotlight actions"
          content={<SpotlighPlayground />}
        />
      </Accordion>
    </>
  );
}
