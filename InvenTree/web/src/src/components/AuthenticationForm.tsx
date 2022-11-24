import { useToggle, upperFirst } from '@mantine/hooks';
import { useForm } from '@mantine/form';
import {
  TextInput,
  PasswordInput,
  Text,
  Paper,
  Group,
  Button,
  Divider,
  Anchor,
  Stack,
  Center
} from '@mantine/core';
import { EditButton } from './items/EditButton';

export function AuthenticationForm({
  Login,
  Register,
  hostname,
  lastUsername,
  editing,
  setEditing,
  selectElement
}: {
  Login: (username: string, password: string) => void;
  Register: (name: string, username: string, password: string) => void;
  hostname: string;
  lastUsername: string;
  editing: boolean;
  setEditing: (value?: React.SetStateAction<boolean> | undefined) => void;
  selectElement: JSX.Element;
}) {
  const [action, toggleAction] = useToggle(['login', 'register']);
  const form = useForm({
    initialValues: {
      email: lastUsername,
      name: '',
      password: '',
      terms: false
    }
  });
  const submit = () => {
    if (action === 'login') {
      Login(form.values.email, form.values.password);
    } else {
      Register(form.values.name, form.values.email, form.values.password);
    }
  };

  return (
    <Paper radius="md" p="xl" withBorder>
      <Text size="lg" weight={500}>Welcome {action} to <Group>
        {(!editing) ? hostname : selectElement}{EditButton(setEditing, editing)}</Group>
      </Text>
      <Center>
        <Group grow mb="md" mt="md">
          <Text>Placeholder</Text>
        </Group>
      </Center>
      <Divider label="Or continue with email" labelPosition="center" my="lg" />
      <form
        onSubmit={form.onSubmit(() => {
          submit();
        })}
      >
        <Stack>
          {action === 'register' && (
            <TextInput
              label="Name"
              placeholder="Your name"
              value={form.values.name}
              onChange={(event) =>
                form.setFieldValue('name', event.currentTarget.value)
              }
            />
          )}

          <TextInput
            required
            label="Username"
            placeholder="hello@mantine.dev"
            value={form.values.email}
            onChange={(event) =>
              form.setFieldValue('email', event.currentTarget.value)
            }
            error={form.errors.email && 'Invalid email'}
          />

          <PasswordInput
            required
            label="Password"
            placeholder="Your password"
            value={form.values.password}
            onChange={(event) =>
              form.setFieldValue('password', event.currentTarget.value)
            }
            error={
              form.errors.password &&
              'Password should include at least 6 characters'
            }
          />
        </Stack>

        <Group position="apart" mt="xl">
          <Anchor
            component="button"
            type="button"
            color="dimmed"
            onClick={() => toggleAction()}
            size="xs"
          >
            {action === 'register'
              ? 'Already have an account? Login'
              : "Don't have an account? Register"}
          </Anchor>
          <Button type="submit">{upperFirst(action)}</Button>
        </Group>
      </form>
    </Paper>
  );
}
