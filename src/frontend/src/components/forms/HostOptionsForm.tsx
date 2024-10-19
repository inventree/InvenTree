import { Trans, t } from '@lingui/macro';
import {
  ActionIcon,
  Box,
  Button,
  Group,
  Space,
  Text,
  TextInput
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { randomId } from '@mantine/hooks';
import { IconSquarePlus, IconTrash } from '@tabler/icons-react';

import type { HostList } from '../../states/states';

export function HostOptionsForm({
  data,
  saveOptions
}: Readonly<{
  data: HostList;
  saveOptions: (newData: HostList) => void;
}>) {
  const form = useForm({ initialValues: data });
  function deleteItem(key: string) {
    const newData = form.values;
    delete newData[key];
    form.setValues(newData);
  }

  const fields = Object.entries(form.values).map(([key]) => (
    <Group key={key} mt='xs'>
      {form.values[key] !== undefined && (
        <>
          <TextInput
            placeholder={t`Host`}
            withAsterisk
            style={{ flex: 1 }}
            {...form.getInputProps(`${key}.host`)}
          />
          <TextInput
            placeholder={t`Name`}
            withAsterisk
            style={{ flex: 1 }}
            {...form.getInputProps(`${key}.name`)}
          />
          <ActionIcon
            color='red'
            onClick={() => {
              deleteItem(key);
            }}
            variant='default'
          >
            <IconTrash />
          </ActionIcon>
        </>
      )}
    </Group>
  ));

  return (
    <form onSubmit={form.onSubmit(saveOptions)}>
      <Box style={{ maxWidth: 500 }} mx='auto'>
        {fields.length > 0 ? (
          <Group mb='xs'>
            <Text fw={500} size='sm' style={{ flex: 1 }}>
              <Trans>Host</Trans>
            </Text>
            <Text fw={500} size='sm' style={{ flex: 1 }}>
              <Trans>Name</Trans>
            </Text>
          </Group>
        ) : (
          <Text c='dimmed' ta='center'>
            <Trans>No one here...</Trans>
          </Text>
        )}
        {fields}
        <Group mt='md'>
          <Button
            onClick={() =>
              form.setFieldValue(`${randomId()}`, { name: '', host: '' })
            }
          >
            <IconSquarePlus />
            <Trans>Add Host</Trans>
          </Button>
          <Space style={{ flex: 1 }} />
          <Button type='submit'>
            <Trans>Save</Trans>
          </Button>
        </Group>
      </Box>
    </form>
  );
}
