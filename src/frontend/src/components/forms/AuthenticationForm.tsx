import { Trans, t } from '@lingui/macro';
import {
  Anchor,
  Button,
  Group,
  Loader,
  PasswordInput,
  Stack,
  Text,
  TextInput
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { useDisclosure } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import { IconCheck } from '@tabler/icons-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { doClassicLogin, doSimpleLogin } from '../../functions/auth';
import { apiUrl, useServerApiState } from '../../states/ApiState';

export function AuthenticationForm() {
  const classicForm = useForm({
    initialValues: { username: '', password: '' }
  });
  const simpleForm = useForm({ initialValues: { email: '' } });
  const [classicLoginMode, setMode] = useDisclosure(true);
  const [auth_settings] = useServerApiState((state) => [state.auth_settings]);
  const navigate = useNavigate();

  const [isLoggingIn, setIsLoggingIn] = useState<boolean>(false);

  function handleLogin() {
    setIsLoggingIn(true);

    if (classicLoginMode === true) {
      doClassicLogin(
        classicForm.values.username,
        classicForm.values.password
      ).then((ret) => {
        setIsLoggingIn(false);

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
        setIsLoggingIn(false);

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
    <form onSubmit={classicForm.onSubmit(() => {})}>
      {classicLoginMode ? (
        <Stack spacing={0}>
          <TextInput
            required
            label={t`Username`}
            placeholder={t`Your username`}
            {...classicForm.getInputProps('username')}
          />
          <PasswordInput
            required
            label={t`Password`}
            placeholder={t`Your password`}
            {...classicForm.getInputProps('password')}
          />
          {auth_settings?.password_forgotten_enabled === true && (
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
          )}
        </Stack>
      ) : (
        <Stack>
          <TextInput
            required
            label={t`Email`}
            description={t`We will send you a link to login - if you are registered`}
            placeholder="email@example.org"
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
            <Trans>Use username and password</Trans>
          )}
        </Anchor>
        <Button type="submit" disabled={isLoggingIn} onClick={handleLogin}>
          {isLoggingIn ? (
            <Loader size="sm" />
          ) : (
            <>
              {classicLoginMode ? (
                <Trans>Log In</Trans>
              ) : (
                <Trans>Send Email</Trans>
              )}
            </>
          )}
        </Button>
      </Group>
    </form>
  );
}

export function RegistrationForm() {
  const registrationForm = useForm({
    initialValues: { username: '', email: '', password1: '', password2: '' }
  });
  const navigate = useNavigate();
  const [isRegistering, setIsRegistering] = useState<boolean>(false);

  function handleRegistration() {
    setIsRegistering(true);
    api
      .post(apiUrl(ApiEndpoints.user_register), registrationForm.values, {
        headers: { Authorization: '' }
      })
      .then((ret) => {
        if (ret?.status === 204) {
          setIsRegistering(false);
          notifications.show({
            title: t`Registration successful`,
            message: t`Please confirm your email address to complete the registration`,
            color: 'green',
            icon: <IconCheck size="1rem" />
          });
          navigate('/home');
        }
      })
      .catch((err) => {
        if (err.response.status === 400) {
          setIsRegistering(false);
          for (const [key, value] of Object.entries(err.response.data)) {
            registrationForm.setFieldError(key, value as string);
          }
          let err_msg = '';
          if (err.response?.data?.non_field_errors) {
            err_msg = err.response.data.non_field_errors;
          }
          notifications.show({
            title: t`Input error`,
            message: t`Check your input and try again. ` + err_msg,
            color: 'red',
            autoClose: 30000
          });
        }
      });
  }

  return (
    <form onSubmit={registrationForm.onSubmit(() => {})}>
      <Stack spacing={0}>
        <TextInput
          required
          label={t`Username`}
          placeholder={t`Your username`}
          {...registrationForm.getInputProps('username')}
        />
        <TextInput
          required
          label={t`Email`}
          description={t`This will be used for a confirmation`}
          placeholder="email@example.org"
          {...registrationForm.getInputProps('email')}
        />
        <PasswordInput
          required
          label={t`Password`}
          placeholder={t`Your password`}
          {...registrationForm.getInputProps('password1')}
        />
        <PasswordInput
          required
          label={t`Password repeat`}
          placeholder={t`Repeat password`}
          {...registrationForm.getInputProps('password2')}
        />
      </Stack>

      <Group position="apart" mt="xl">
        <Button
          type="submit"
          disabled={isRegistering}
          onClick={handleRegistration}
          fullWidth
        >
          <Trans>Register</Trans>
        </Button>
      </Group>
    </form>
  );
}

export function ModeSelector({
  loginMode,
  setMode
}: {
  loginMode: boolean;
  setMode: any;
}) {
  const [auth_settings] = useServerApiState((state) => [state.auth_settings]);

  if (auth_settings?.registration_enabled === false) return null;
  return (
    <Text ta="center" size={'xs'} mt={'md'}>
      {loginMode ? (
        <>
          <Trans>Don&apos;t have an account?</Trans>{' '}
          <Anchor
            component="button"
            type="button"
            color="dimmed"
            size="xs"
            onClick={() => setMode.close()}
          >
            <Trans>Register</Trans>
          </Anchor>
        </>
      ) : (
        <Anchor
          component="button"
          type="button"
          color="dimmed"
          size="xs"
          onClick={() => setMode.open()}
        >
          <Trans>Go back to login</Trans>
        </Anchor>
      )}
    </Text>
  );
}
