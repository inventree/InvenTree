import { Trans } from '@lingui/macro';
import { Alert, Group, Stack } from '@mantine/core';
import { Button } from '@mantine/core';
import {
  IconBuilding,
  IconGlobe,
  IconKey,
  IconMail,
  IconUser
} from '@tabler/icons-react';
import { useState } from 'react';

import { ApiForm, ApiFormFieldType } from '../../components/forms/ApiForm';
import { CreateApiForm } from '../../components/forms/CreateApiForm';
import { DeleteApiForm } from '../../components/forms/DeleteApiForm';
import { EditApiForm } from '../../components/forms/EditApiForm';
import { PlaceholderPill } from '../../components/items/Placeholder';
import { StylishText } from '../../components/items/StylishText';

export default function Home() {
  const [partFormOpened, setPartFormOpened] = useState(false);
  const [poFormOpened, setPoFormOpened] = useState(false);
  const [companyFormOpened, setCompanyFormOpened] = useState(false);
  const [stockFormOpened, setStockFormOpened] = useState(false);
  const [salesOrderFormOpened, setSalesOrderFormOpened] = useState(false);

  const partFields: ApiFormFieldType[] = [
    {
      name: 'name'
    },
    {
      name: 'description'
    },
    {
      name: 'keywords',
      icon: <IconKey />
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
    },
    {
      name: 'minimum_stock'
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
    }
  ];

  const companyFields: ApiFormFieldType[] = [
    {
      name: 'name'
    },
    {
      name: 'description'
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
        opened={partFormOpened}
        onClose={() => setPartFormOpened(false)}
      />
      <EditApiForm
        name="po-edit"
        url="/order/po/"
        pk={1}
        fields={poFields}
        title="Edit Purchase Order"
        opened={poFormOpened}
        onClose={() => setPoFormOpened(false)}
      />
      <EditApiForm
        name="company-edit"
        url="/company/"
        pk={1}
        fields={companyFields}
        title="Edit Company"
        opened={companyFormOpened}
        onClose={() => setCompanyFormOpened(false)}
      />
      <DeleteApiForm
        name="stock-delete"
        url="/stock/"
        title="Delete Stock Item"
        pk={1}
        fields={[]}
        opened={stockFormOpened}
        onClose={() => setStockFormOpened(false)}
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
        opened={salesOrderFormOpened}
        onClose={() => setSalesOrderFormOpened(false)}
      />

      <Stack align="flex-start" spacing="xs">
        <Button
          onClick={() => setPartFormOpened(true)}
          variant="outline"
          color="blue"
        >
          Edit Part Form
        </Button>
        <Button
          variant="outline"
          color="blue"
          onClick={() => setPoFormOpened(true)}
        >
          Edit Purchase Order Form
        </Button>
        <Button
          variant="outline"
          color="blue"
          onClick={() => setCompanyFormOpened(true)}
        >
          Edit Company Form
        </Button>
        <Button
          variant="outline"
          color="green"
          onClick={() => setSalesOrderFormOpened(true)}
        >
          Create Sales Order Form
        </Button>
        <Button
          variant="outline"
          color="red"
          onClick={() => setStockFormOpened(true)}
        >
          Delete Stock Item Form
        </Button>
      </Stack>
    </>
  );
}
