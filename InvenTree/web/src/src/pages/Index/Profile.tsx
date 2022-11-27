import {
  Button,
  Container,
  Grid,
  Group,
  SimpleGrid,
  Skeleton,
  Tabs,
  Text,
  TextInput
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { useNavigate, useParams } from 'react-router-dom';
import { StylishText } from '../../components/items/StylishText';
import { InvenTreeStyle } from '../../globalStyle';
import { useToggle } from '@mantine/hooks';
import { useQuery } from '@tanstack/react-query';
import { api, queryClient } from '../../App';
import { EditButton } from '../../components/items/EditButton';
import { Trans } from '@lingui/macro'


export function Profile() {
  const navigate = useNavigate();
  const { tabValue } = useParams();

  return (
    <>
      <StylishText><Trans>Profile</Trans></StylishText>
      <Tabs
        orientation="vertical"
        value={tabValue}
        onTabChange={(value) => navigate(`/profile/${value}`)}
      >
        <Tabs.List>
          <Tabs.Tab value="user"><Trans>User</Trans></Tabs.Tab>
          <Tabs.Tab value="settings"><Trans>Settings</Trans></Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="user">
          <UserPanel />
        </Tabs.Panel>
        <Tabs.Panel value="settings">
          <SettingsPanel />
        </Tabs.Panel>
      </Tabs>
    </>
  );
}

function UserPanel() {
  // view
  const { theme } = InvenTreeStyle();
  const PRIMARY_COL_HEIGHT = 300;
  const SECONDARY_COL_HEIGHT = PRIMARY_COL_HEIGHT / 2 - theme.spacing.md / 2;

  // data
  function fetchData() {
    return api.get('user/me/').then((res) => res.data);
  }
  const { isLoading, data } = useQuery({
    queryKey: ['user-me'],
    queryFn: fetchData
  });

  return (
    <Container>
      <SimpleGrid cols={2} spacing="md">
        <Container w="100%">
          {isLoading ? (
            <Skeleton height="100%" radius="md" />
          ) : (
            <UserInfo data={data} />
          )}
        </Container>
        <Grid gutter="md">
          <Grid.Col>
            <Skeleton height={SECONDARY_COL_HEIGHT} radius="md" />
          </Grid.Col>
          <Grid.Col span={6}>
            <Skeleton height={SECONDARY_COL_HEIGHT} radius="md" />
          </Grid.Col>
          <Grid.Col span={6}>
            <Skeleton height={SECONDARY_COL_HEIGHT} radius="md" />
          </Grid.Col>
        </Grid>
      </SimpleGrid>
    </Container>
  );
}

function UserInfo({ data }: { data: any }) {
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
        <Text><Trans>Userinfo</Trans></Text>
        {EditButton(setEditing, editing)}
      </Group>
      <Group>
        {editing ? (
          <TextInput
            label="First name"
            placeholder="First name"
            {...form.getInputProps('first_name')}
          />
        ) : (
          <Text><Trans>First name: {form.values.first_name}</Trans></Text>
        )}
        {editing ? (
          <TextInput
            label="Last name"
            placeholder="Last name"
            {...form.getInputProps('last_name')}
          />
        ) : (
          <Text><Trans>Last name: {form.values.last_name}</Trans></Text>
        )}
        {editing ? (
          <TextInput
            label="Username"
            placeholder="Username"
            {...form.getInputProps('username')}
          />
        ) : (
          <Text><Trans>Username: {form.values.username}</Trans></Text>
        )}
      </Group>
      {editing ? (
        <Group position="right" mt="md">
          <Button type="submit"><Trans>Submit</Trans></Button>
        </Group>
      ) : null}
    </form>
  );
}

function SettingsPanel() {
  return (
    <Container>
      <Text><Trans>Settings</Trans></Text>
    </Container>
  );
}
