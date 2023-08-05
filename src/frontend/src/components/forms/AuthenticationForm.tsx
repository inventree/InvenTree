import { Trans, t } from '@lingui/macro';
import {
  Anchor,
  Button,
  Group,
  Paper,
  PasswordInput,
  Stack,
  Text,
  TextInput
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { useDisclosure } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import { IconCheck } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';

import { doClassicLogin, doSimpleLogin } from '../../functions/auth';

export function AuthenticationForm() {
  const classicForm = useForm({
    initialValues: { username: '', password: '' }
  });
  const simpleForm = useForm({ initialValues: { email: '' } });
  const [classicLoginMode, setMode] = useDisclosure(true);
  const navigate = useNavigate();

  function handleLogin() {
    if (classicLoginMode === true) {
      doClassicLogin(
        classicForm.values.username,
        classicForm.values.password
      ).then((ret) => {
        if (ret === false) {
          notifications.show({
            title: t`Login failed`,
            message: t`Check your input and try again.`,
            color: 'red'
          });
        } else {
          notifications.show({
            title: t`Login successful`,
            message: t`Welcome back!`,
            color: 'green',
            icon: <IconCheck size="1rem" />
          });
          navigate('/home');
        }
      });
    } else {
      doSimpleLogin(simpleForm.values.email).then((ret) => {
        if (ret?.status === 'ok') {
          notifications.show({
            title: t`Mail delivery successful`,
            message: t`Check your inbox for the login link. If you have an account, you will receive a login link. Check in spam too.`,
            color: 'green',
            icon: <IconCheck size="1rem" />,
            autoClose: false
          });
        } else {
          notifications.show({
            title: t`Input error`,
            message: t`Check your input and try again.`,
            color: 'red'
          });
        }
      });
    }
  }

  return (
    <Paper radius="md" p="xl" withBorder>
      <Text size="lg" weight={500}>
        <Trans>Welcome, log in below</Trans>
      </Text>
      <form onSubmit={classicForm.onSubmit(() => {})}>
        {classicLoginMode ? (
          <Stack>
            <TextInput
              required
              label={t`Username`}
              placeholder="reader"
              {...classicForm.getInputProps('username')}
            />
            <PasswordInput
              required
              label={t`Password`}
              placeholder={t`Your password`}
              {...classicForm.getInputProps('password')}
            />
            <Group position="apart" mt="0">
              <Anchor
                component="button"
                type="button"
                color="dimmed"
                size="xs"
                onClick={() => navigate('/reset-password')}
              >
                <Trans>Reset password</Trans>
              </Anchor>
            </Group>
          </Stack>
        ) : (
          <Stack>
            <TextInput
              required
              label={t`Email`}
              description={t`We will send you a link to login - if you are registered`}
              placeholder="reader@example.org"
              {...simpleForm.getInputProps('email')}
            />
          </Stack>
        )}

        <Group position="apart" mt="xl">
          <Anchor
            component="button"
            type="button"
            color="dimmed"
            size="xs"
            onClick={() => setMode.toggle()}
          >
            {classicLoginMode ? (
              <Trans>Send me an email</Trans>
            ) : (
              <Trans>I will use username and password</Trans>
            )}
          </Anchor>
          <Button type="submit" onClick={handleLogin}>
            {classicLoginMode ? (
              <Trans>Log in</Trans>
            ) : (
              <Trans>Send mail</Trans>
            )}
          </Button>
        </Group>
      </form>
    </Paper>
  );
}
