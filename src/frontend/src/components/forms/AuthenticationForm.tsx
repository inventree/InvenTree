import { Trans, t } from '@lingui/macro';
import {
  Anchor,
  Button,
  Divider,
  Group,
  Loader,
  PasswordInput,
  Stack,
  Text,
  TextInput
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { useDisclosure } from '@mantine/hooks';
import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import { showNotification } from '@mantine/notifications';
import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import {
  doBasicLogin,
  doSimpleLogin,
  followRedirect
} from '../../functions/auth';
import { showLoginNotification } from '../../functions/notifications';
import { apiUrl, useServerApiState } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { SsoButton } from '../buttons/SSOButton';

export function AuthenticationForm() {
  const classicForm = useForm({
    initialValues: { username: '', password: '' }
  });
  const simpleForm = useForm({ initialValues: { email: '' } });
  const [classicLoginMode, setMode] = useDisclosure(true);
  const [auth_settings] = useServerApiState((state) => [state.auth_settings]);
  const navigate = useNavigate();
  const location = useLocation();
  const { isLoggedIn } = useUserState();

  const [isLoggingIn, setIsLoggingIn] = useState<boolean>(false);

  function handleLogin() {
    setIsLoggingIn(true);

    if (classicLoginMode === true) {
      doBasicLogin(classicForm.values.username, classicForm.values.password)
        .then(() => {
          setIsLoggingIn(false);

          if (isLoggedIn()) {
            showLoginNotification({
              title: t`Login successful`,
              message: t`Logged in successfully`
            });
            followRedirect(navigate, location?.state);
          } else {
            showLoginNotification({
              title: t`Login failed`,
              message: t`Check your input and try again.`,
              success: false
            });
          }
        })
        .catch(() => {
          showNotification({
            title: t`Login failed`,
            message: t`Check your input and try again.`,
            color: 'red'
          });
        });
    } else {
      doSimpleLogin(simpleForm.values.email).then((ret) => {
        setIsLoggingIn(false);

        if (ret?.status === 'ok') {
          showLoginNotification({
            title: t`Mail delivery successful`,
            message: t`Check your inbox for the login link. If you have an account, you will receive a login link. Check in spam too.`
          });
        } else {
          showLoginNotification({
            title: t`Mail delivery failed`,
            message: t`Check your input and try again.`,
            success: false
          });
        }
      });
    }
  }

  return (
    <>
      {auth_settings?.sso_enabled === true ? (
        <>
          <Group grow mb='md' mt='md'>
            {auth_settings.providers.map((provider) => (
              <SsoButton provider={provider} key={provider.id} />
            ))}
          </Group>

          <Divider
            label={t`Or continue with other methods`}
            labelPosition='center'
            my='lg'
          />
        </>
      ) : null}
      <form onSubmit={classicForm.onSubmit(() => {})}>
        {classicLoginMode ? (
          <Stack gap={0}>
            <TextInput
              required
              label={t`Username`}
              aria-label='login-username'
              placeholder={t`Your username`}
              {...classicForm.getInputProps('username')}
            />
            <PasswordInput
              required
              label={t`Password`}
              aria-label='login-password'
              placeholder={t`Your password`}
              {...classicForm.getInputProps('password')}
            />
            {auth_settings?.password_forgotten_enabled === true && (
              <Group justify='space-between' mt='0'>
                <Anchor
                  component='button'
                  type='button'
                  c='dimmed'
                  size='xs'
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
              placeholder='email@example.org'
              {...simpleForm.getInputProps('email')}
            />
          </Stack>
        )}

        <Group justify='space-between' mt='xl'>
          <Anchor
            component='button'
            type='button'
            c='dimmed'
            size='xs'
            onClick={() => setMode.toggle()}
          >
            {classicLoginMode ? (
              <Trans>Send me an email</Trans>
            ) : (
              <Trans>Use username and password</Trans>
            )}
          </Anchor>
          <Button type='submit' disabled={isLoggingIn} onClick={handleLogin}>
            {isLoggingIn ? (
              <Loader size='sm' />
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
    </>
  );
}

export function RegistrationForm() {
  const registrationForm = useForm({
    initialValues: { username: '', email: '', password1: '', password2: '' }
  });
  const navigate = useNavigate();
  const [auth_settings] = useServerApiState((state) => [state.auth_settings]);
  const [isRegistering, setIsRegistering] = useState<boolean>(false);

  function handleRegistration() {
    setIsRegistering(true);
    api
      .post(apiUrl(ApiEndpoints.user_register), registrationForm.values, {
        headers: { Authorization: '' }
      })
      .then((ret) => {
        if (ret?.status === 204 || ret?.status === 201) {
          setIsRegistering(false);
          showLoginNotification({
            title: t`Registration successful`,
            message: t`Please confirm your email address to complete the registration`
          });
          navigate('/home');
        }
      })
      .catch((err) => {
        if (err.response?.status === 400) {
          setIsRegistering(false);
          for (const [key, value] of Object.entries(err.response.data)) {
            registrationForm.setFieldError(key, value as string);
          }
          let err_msg = '';
          if (err.response?.data?.non_field_errors) {
            err_msg = err.response.data.non_field_errors;
          }
          showLoginNotification({
            title: t`Input error`,
            message: t`Check your input and try again. ` + err_msg,
            success: false
          });
        }
      });
  }

  const both_reg_enabled =
    auth_settings?.registration_enabled && auth_settings?.sso_registration;
  return (
    <>
      {auth_settings?.registration_enabled && (
        <form onSubmit={registrationForm.onSubmit(() => {})}>
          <Stack gap={0}>
            <TextInput
              required
              label={t`Username`}
              aria-label='register-username'
              placeholder={t`Your username`}
              {...registrationForm.getInputProps('username')}
            />
            <TextInput
              required
              label={t`Email`}
              aria-label='register-email'
              description={t`This will be used for a confirmation`}
              placeholder='email@example.org'
              {...registrationForm.getInputProps('email')}
            />
            <PasswordInput
              required
              label={t`Password`}
              aria-label='register-password'
              placeholder={t`Your password`}
              {...registrationForm.getInputProps('password1')}
            />
            <PasswordInput
              required
              label={t`Password repeat`}
              aria-label='register-password-repeat'
              placeholder={t`Repeat password`}
              {...registrationForm.getInputProps('password2')}
            />
          </Stack>

          <Group justify='space-between' mt='xl'>
            <Button
              type='submit'
              disabled={isRegistering}
              onClick={handleRegistration}
              fullWidth
            >
              <Trans>Register</Trans>
            </Button>
          </Group>
        </form>
      )}
      {both_reg_enabled && (
        <Divider label={t`Or use SSO`} labelPosition='center' my='lg' />
      )}
      {auth_settings?.sso_registration === true && (
        <Group grow mb='md' mt='md'>
          {auth_settings.providers.map((provider) => (
            <SsoButton provider={provider} key={provider.id} />
          ))}
        </Group>
      )}
    </>
  );
}

export function ModeSelector({
  loginMode,
  setMode
}: Readonly<{
  loginMode: boolean;
  setMode: any;
}>) {
  const [auth_settings] = useServerApiState((state) => [state.auth_settings]);
  const registration_enabled =
    auth_settings?.registration_enabled ||
    auth_settings?.sso_registration ||
    false;

  if (registration_enabled === false) return null;
  return (
    <Text ta='center' size={'xs'} mt={'md'}>
      {loginMode ? (
        <>
          <Trans>Don&apos;t have an account?</Trans>{' '}
          <Anchor
            component='button'
            type='button'
            c='dimmed'
            size='xs'
            onClick={() => setMode.close()}
          >
            <Trans>Register</Trans>
          </Anchor>
        </>
      ) : (
        <Anchor
          component='button'
          type='button'
          c='dimmed'
          size='xs'
          onClick={() => setMode.open()}
        >
          <Trans>Go back to login</Trans>
        </Anchor>
      )}
    </Text>
  );
}
