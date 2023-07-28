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
  IconVersions
} from '@tabler/icons-react';
import { title } from 'process';
import { useState } from 'react';

import { ApiForm, ApiFormFieldType } from '../../components/forms/ApiForm';
import { CreateApiForm } from '../../components/forms/CreateApiForm';
import { DeleteApiForm } from '../../components/forms/DeleteApiForm';
import { EditApiForm } from '../../components/forms/EditApiForm';
import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';
import { openEditApiForm, openModalApiForm } from '../../functions/forms';

export default function Home() {
  const [modalIdx, setModalIdx] = useState<number>(0);

  const partFields: ApiFormFieldType[] = [
    {
      name: 'category'
    },
    {
      name: 'name'
    },
    {
      name: 'IPN'
    },
    {
      name: 'revision',
      icon: <IconVersions />
    },
    {
      name: 'description'
    },
    {
      name: 'variant_of',
      icon: <IconSitemap />
    },
    {
      name: 'keywords',
      icon: <IconKey />
    },
    {
      name: 'units'
    },
    {
      name: 'link',
      icon: <IconLink />
    },
    {
      name: 'assembly'
    },
    {
      name: 'trackable'
    },
    {
      name: 'virtual'
    },
    {
      name: 'minimum_stock',
      icon: <IconAlertCircle />
    }
  ];

  const poFields: ApiFormFieldType[] = [
    {
      name: 'reference'
    },
    {
      name: 'supplier'
    },
    {
      name: 'target_date'
    },
    {
      name: 'status'
    }
  ];

  const salesOrderFields: ApiFormFieldType[] = [
    {
      name: 'reference'
    },
    {
      name: 'customer'
    },
    {
      name: 'description'
    },
    {
      name: 'status'
    }
  ];

  const companyFields: ApiFormFieldType[] = [
    {
      name: 'name'
    },
    {
      name: 'description',
      hidden: true
    },
    {
      name: 'website',
      icon: <IconGlobe />
    },
    {
      name: 'email',
      icon: <IconMail />
    },
    {
      name: 'contact',
      icon: <IconUser />
    },
    {
      name: 'is_customer'
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
      <EditApiForm
        name="part-edit"
        url="/part/"
        pk={1}
        fields={partFields}
        title="Edit Part"
        opened={modalIdx == 1}
        onClose={() => setModalIdx(0)}
      />
      <EditApiForm
        name="po-edit"
        url="/order/po/"
        pk={1}
        fields={poFields}
        title="Edit Purchase Order"
        opened={modalIdx == 2}
        onClose={() => setModalIdx(0)}
      />
      <EditApiForm
        name="company-edit"
        url="/company/"
        pk={1}
        fields={companyFields}
        title="Edit Company"
        opened={modalIdx == 3}
        onClose={() => setModalIdx(0)}
      />
      <DeleteApiForm
        name="stock-delete"
        url="/stock/"
        title="Delete Stock Item"
        pk={1}
        fields={[]}
        opened={modalIdx == 4}
        onClose={() => setModalIdx(0)}
        preFormContent={<Alert color="red">Are you sure?</Alert>}
        postFormContentFunc={() => (
          <Alert color="blue">Post form content!</Alert>
        )}
      />
      <CreateApiForm
        name="sales-order-create"
        url="/order/so/"
        title="Create Sales Order"
        fields={salesOrderFields}
        opened={modalIdx == 5}
        onClose={() => setModalIdx(0)}
      />

      <CreateApiForm
        name="invalid-url-form"
        url="/orderr/so/"
        title="Create Sales Order (wrong URL)"
        preFormContent={<Alert color="red">This form has the wrong URL</Alert>}
        opened={modalIdx == 6}
        onClose={() => setModalIdx(0)}
        fields={[]}
      />

      <CreateApiForm
        name="invalid-url-form"
        url="/order/so/"
        pk={1}
        title="Create Sales Order (wrong method)"
        preFormContent={
          <Alert color="red">This form has the wrong method</Alert>
        }
        opened={modalIdx == 7}
        onClose={() => setModalIdx(0)}
        fields={[]}
      />

      <Space />
      <Text size="xl">Working Forms</Text>
      <SimpleGrid cols={4}>
        <Button onClick={() => setModalIdx(1)} variant="outline" color="blue">
          Edit Part Form
        </Button>
        <Button variant="outline" color="blue" onClick={() => setModalIdx(2)}>
          Edit Purchase Order Form
        </Button>
        <Button variant="outline" color="blue" onClick={() => setModalIdx(3)}>
          Edit Company Form
        </Button>
        <Button variant="outline" color="green" onClick={() => setModalIdx(4)}>
          Create Sales Order Form
        </Button>
        <Button variant="outline" color="red" onClick={() => setModalIdx(5)}>
          Delete Stock Item Form
        </Button>
      </SimpleGrid>
      <Text size="xl">Broken Forms</Text>
      <SimpleGrid cols={4}>
        <Button variant="outline" color="yellow" onClick={() => setModalIdx(6)}>
          Invalid URL
        </Button>
        <Button variant="outline" color="yellow" onClick={() => setModalIdx(7)}>
          Wrong Method
        </Button>
        <Button
          variant="outline"
          color="lime"
          onClick={() =>
            openEditApiForm({
              title: 'A test dynamic form',
              props: {
                name: 'my form',
                onClose: () => {
                  console.log('closed!');
                },
                url: '/part/',
                pk: 3,
                method: 'PUT',
                title: 'a title',
                fields: [],
                opened: false
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
