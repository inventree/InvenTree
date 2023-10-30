import { Trans } from '@lingui/macro';
import {
  Button,
  Group,
  Skeleton,
  Stack,
  Text,
  TextInput,
  Title
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { useToggle } from '@mantine/hooks';

import { api, queryClient } from '../../../../App';
import { EditButton } from '../../../../components/items/EditButton';
import { ApiPaths, apiUrl } from '../../../../states/ApiState';
import { UserProps } from '../../../../states/states';

export function AccountDetailPanel({ data }: { data: UserProps | undefined }) {
  if (!data) return <Skeleton />;

  const form = useForm({ initialValues: data });
  const [editing, setEditing] = useToggle([false, true] as const);
  function SaveData(values: any) {
    api.put(apiUrl(ApiPaths.user_me), values).then((res) => {
      if (res.status === 200) {
        setEditing();
        queryClient.invalidateQueries({ queryKey: ['user-me'] });
      }
    });
  }

  return (
    <form onSubmit={form.onSubmit((values) => SaveData(values))}>
      <Group>
        <Title order={3}>
          <Trans>Account Details</Trans>
        </Title>
        <EditButton setEditing={setEditing} editing={editing} />
      </Group>
      <Group>
        {editing ? (
          <Stack spacing="xs">
            <TextInput
              label="First name"
              placeholder="First name"
              {...form.getInputProps('first_name')}
            />
            <TextInput
              label="Last name"
              placeholder="Last name"
              {...form.getInputProps('last_name')}
            />
            <TextInput
              label="Username"
              placeholder="Username"
              {...form.getInputProps('username')}
            />
            <Group position="right" mt="md">
              <Button type="submit">
                <Trans>Submit</Trans>
              </Button>
            </Group>
          </Stack>
        ) : (
          <Stack spacing="0">
            <Text>
              <Trans>First name: {form.values.first_name}</Trans>
            </Text>
            <Text>
              <Trans>Last name: {form.values.last_name}</Trans>
            </Text>
            <Text>
              <Trans>Username: {form.values.username}</Trans>
            </Text>
          </Stack>
        )}
      </Group>
    </form>
  );
}
