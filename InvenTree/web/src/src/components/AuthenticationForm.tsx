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
import { Trans, t } from '@lingui/macro'


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
  const actionname = action === 'login' ? t`login` : t`register`;
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
      <Text size="lg" weight={500}><Trans>Welcome {actionname} to </Trans><Group>
        {(!editing) ? hostname : selectElement}{EditButton(setEditing, editing)}</Group>
      </Text>
      <Center>
        <Group grow mb="md" mt="md">
          <Text><Trans>Placeholder</Trans></Text>
        </Group>
      </Center>
      <Divider label={<Trans>Or continue with email</Trans>} labelPosition="center" my="lg" />
      <form
        onSubmit={form.onSubmit(() => {
          submit();
        })}
      >
        <Stack>
          {action === 'register' && (
            <TextInput
              label={<Trans>Name</Trans>}
              placeholder={t`Your name`}
              value={form.values.name}
              onChange={(event) =>
                form.setFieldValue('name', event.currentTarget.value)
              }
            />
          )}

          <TextInput
            required
            label={<Trans>Username</Trans>}
            placeholder="hello@mantine.dev"
            value={form.values.email}
            onChange={(event) =>
              form.setFieldValue('email', event.currentTarget.value)
            }
            error={form.errors.email && <Trans>Invalid email</Trans>}
          />

          <PasswordInput
            required
            label={<Trans>Password</Trans>}
            placeholder={t`Your password`}
            value={form.values.password}
            onChange={(event) =>
              form.setFieldValue('password', event.currentTarget.value)
            }
            error={form.errors.password && <Trans>Password should include at least 6 characters</Trans>}
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
              ? <Trans>Already have an account? Login</Trans>
              : <Trans>Don't have an account? Register</Trans>}
          </Anchor>
          <Button type="submit">{upperFirst(actionname)}</Button>
        </Group>
      </form>
    </Paper>
  );
}
