import { Trans, t } from '@lingui/macro';
import {
  Anchor,
  Button,
  Divider,
  Group,
  Loader,
  PasswordInput,
  Stack,
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
  ensureCsrf,
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
  const [auth_config, sso_enabled, password_forgotten_enabled] =
    useServerApiState((state) => [
      state.auth_config,
      state.sso_enabled,
      state.password_forgotten_enabled
    ]);
  const navigate = useNavigate();
  const location = useLocation();
  const { isLoggedIn } = useUserState();

  const [isLoggingIn, setIsLoggingIn] = useState<boolean>(false);

  function handleLogin() {
    setIsLoggingIn(true);

    if (classicLoginMode === true) {
      doBasicLogin(
        classicForm.values.username,
        classicForm.values.password,
        navigate
      )
        .then((success) => {
          setIsLoggingIn(false);

          if (isLoggedIn()) {
            showLoginNotification({
              title: t`Login successful`,
              message: t`Logged in successfully`
            });
            followRedirect(navigate, location?.state);
          } else if (success) {
            // MFA login
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
      {sso_enabled() ? (
        <>
          <Group grow mb='md' mt='md'>
            {auth_config?.socialaccount.providers.map((provider) => (
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
            {password_forgotten_enabled() === true && (
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
    initialValues: {
      username: '',
      email: '',
      password: '',
      password2: '' as string | undefined
    }
  });
  const navigate = useNavigate();
  const [auth_config, registration_enabled, sso_registration] =
    useServerApiState((state) => [
      state.auth_config,
      state.registration_enabled,
      state.sso_registration_enabled
    ]);
  const [isRegistering, setIsRegistering] = useState<boolean>(false);

  async function handleRegistration() {
    // check if passwords match
    if (
      registrationForm.values.password !== registrationForm.values.password2
    ) {
      registrationForm.setFieldError('password2', t`Passwords do not match`);
      return;
    }
    setIsRegistering(true);

    // remove password2 from the request
    const { password2, ...vals } = registrationForm.values;
    await ensureCsrf();

    api
      .post(apiUrl(ApiEndpoints.auth_signup), vals, {
        headers: { Authorization: '' }
      })
      .then((ret) => {
        if (ret?.status === 200) {
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

          // collect all errors per field
          const errors: { [key: string]: string[] } = {};
          for (const val of err.response.data.errors) {
            if (!errors[val.param]) {
              errors[val.param] = [];
            }
            errors[val.param].push(val.message);
          }

          for (const key in errors) {
            registrationForm.setFieldError(key, errors[key]);
          }

          showLoginNotification({
            title: t`Input error`,
            message: t`Check your input and try again. `,
            success: false
          });
        }
      });
  }

  const both_reg_enabled = registration_enabled() && sso_registration();
  return (
    <>
      {registration_enabled() && (
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
              {...registrationForm.getInputProps('password')}
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
      {sso_registration() && (
        <Group grow mb='md' mt='md'>
          {auth_config?.socialaccount.providers.map((provider) => (
            <SsoButton provider={provider} key={provider.id} />
          ))}
        </Group>
      )}
    </>
  );
}
