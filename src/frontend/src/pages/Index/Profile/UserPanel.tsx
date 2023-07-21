import { Trans } from '@lingui/macro';
import {
  Button,
  Container,
  Grid,
  Group,
  SimpleGrid,
  Skeleton,
  Stack,
  Text,
  TextInput,
  Title
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { useToggle } from '@mantine/hooks';
import { useQuery } from '@tanstack/react-query';

import { api, queryClient } from '../../../App';
import { ColorToggle } from '../../../components/items/ColorToggle';
import { EditButton } from '../../../components/items/EditButton';
import { LanguageSelect } from '../../../components/items/LanguageSelect';
import { useLocalState } from '../../../states/LocalState';
import { UserTheme } from './UserTheme';

export function UserPanel() {
  // view
  const PRIMARY_COL_HEIGHT = 300;
  const SECONDARY_COL_HEIGHT = PRIMARY_COL_HEIGHT / 2 - 8;

  // data
  function fetchData() {
    return api.get('user/me/').then((res) => res.data);
  }
  const { isLoading, data } = useQuery({
    queryKey: ['user-me'],
    queryFn: fetchData
  });

  return (
    <div>
      <SimpleGrid cols={2} spacing="md">
        <Container w="100%">
          {isLoading ? (
            <Skeleton height={SECONDARY_COL_HEIGHT} />
          ) : (
            <UserInfo data={data} />
          )}
        </Container>
        <Grid gutter="md">
          <Grid.Col>
            <UserTheme height={SECONDARY_COL_HEIGHT} />
          </Grid.Col>
          <Grid.Col span={6}>
            <DisplaySettings height={SECONDARY_COL_HEIGHT} />
          </Grid.Col>
          <Grid.Col span={6}>
            <Skeleton height={SECONDARY_COL_HEIGHT} />
          </Grid.Col>
        </Grid>
      </SimpleGrid>
    </div>
  );
}

export function UserInfo({ data }: { data: any }) {
  if (!data) return <Skeleton />;

  const form = useForm({ initialValues: data });
  const [editing, setEditing] = useToggle([false, true] as const);
  function SaveData(values: any) {
    api.put('user/me/', values).then((res) => {
      if (res.status === 200) {
        setEditing();
        queryClient.invalidateQueries(['user-me']);
      }
    });
  }

  return (
    <form onSubmit={form.onSubmit((values) => SaveData(values))}>
      <Group>
        <Title order={3}>
          <Trans>Userinfo</Trans>
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
          <Stack spacing="xs">
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

function DisplaySettings({ height }: { height: number }) {
  function enablePseudoLang(): void {
    useLocalState.setState({ language: 'pseudo-LOCALE' });
  }

  return (
    <Container w="100%" mih={height} p={0}>
      <Title order={3}>
        <Trans>Display Settings</Trans>
      </Title>
      <Group>
        <Text>
          <Trans>Color Mode</Trans>
        </Text>
        <ColorToggle />
      </Group>
      <Group align="top">
        <Text>
          <Trans>Language</Trans>
        </Text>
        <Stack>
          <LanguageSelect />
          <Button onClick={enablePseudoLang} variant="light">
            <Trans>Use pseudo language</Trans>
          </Button>
        </Stack>
      </Group>
    </Container>
  );
}
