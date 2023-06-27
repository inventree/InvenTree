import { useForm } from '@mantine/form';
import {
  TextInput,
  Group,
  ActionIcon,
  Box,
  Text,
  Button,
  Space
} from '@mantine/core';
import { randomId } from '@mantine/hooks';
import { IconTrash, IconSquarePlus } from '@tabler/icons';
import { HostList } from '../context/states';
import { Trans, t } from '@lingui/macro';

export function HostOptionsForm({
  data,
  saveOptions
}: {
  data: HostList;
  saveOptions: (newData: HostList) => void;
}) {
  const form = useForm({ initialValues: data });
  function deleteItem(key: string) {
    const newData = form.values;
    delete newData[key];
    form.setValues(newData);
  }

  const fields = Object.entries(form.values).map(([key]) => (
    <Group key={key} mt="xs">
      {form.values[key] !== undefined && (
        <>
          <TextInput
            placeholder={t`Host`}
            withAsterisk
            sx={{ flex: 1 }}
            {...form.getInputProps(`${key}.host`)}
          />
          <TextInput
            placeholder={t`Name`}
            withAsterisk
            sx={{ flex: 1 }}
            {...form.getInputProps(`${key}.name`)}
          />
          <ActionIcon
            color="red"
            onClick={() => {
              deleteItem(key);
            }}
          >
            <IconTrash size={16} />
          </ActionIcon>
        </>
      )}
    </Group>
  ));

  return (
    <form onSubmit={form.onSubmit(saveOptions)}>
      <Box sx={{ maxWidth: 500 }} mx="auto">
        {fields.length > 0 ? (
          <Group mb="xs">
            <Text weight={500} size="sm" sx={{ flex: 1 }}>
              <Trans>Host</Trans>
            </Text>
            <Text weight={500} size="sm" sx={{ flex: 1 }}>
              <Trans>Name</Trans>
            </Text>
          </Group>
        ) : (
          <Text color="dimmed" align="center">
            <Trans>No one here...</Trans>
          </Text>
        )}
        {fields}
        <Group mt="md">
          <Button
            onClick={() =>
              form.setFieldValue(`${randomId()}`, { name: '', host: '' })
            }
          >
            <IconSquarePlus size={16} />
            <Trans>Add Host</Trans>
          </Button>
          <Space sx={{ flex: 1 }} />
          <Button type="submit">
            <Trans>Save</Trans>
          </Button>
        </Group>
      </Box>
    </form>
  );
}
