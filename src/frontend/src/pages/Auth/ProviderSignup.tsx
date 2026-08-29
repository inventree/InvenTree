import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import { Alert, Button, Group, Stack, Text, TextInput } from '@mantine/core';
import { useForm } from '@mantine/form';
import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { api } from '../../App';
import { handleSuccessFullAuth } from '../../functions/auth';
import { showLoginNotification } from '../../functions/notifications';
import { Wrapper } from './Layout';

/*
 * Completes an SSO login for a user with no matching local account.
 *
 * The server parks these as a pending 'provider_signup' auth flow rather
 * than logging the user in - see checkLoginState() in functions/auth.tsx,
 * which routes here when that flow is detected.
 */
export default function ProviderSignup() {
  const navigate = useNavigate();
  const location = useLocation();

  const form = useForm({ initialValues: { username: '', email: '' } });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [providerName, setProviderName] = useState<string>('');
  const [formError, setFormError] = useState<string | undefined>(undefined);

  useEffect(() => {
    api
      .get(apiUrl(ApiEndpoints.auth_provider_signup))
      .then((response) => {
        const data = response.data?.data ?? {};
        // Suggested email addresses come back as their own list (not on
        // `user`) - prefer the primary one, falling back to the first.
        const emails = data?.email ?? [];
        const email = emails.find((e: any) => e.primary) ?? emails[0];
        form.setValues({
          username: data?.user?.username ?? '',
          email: email?.email ?? ''
        });
        setProviderName(data?.account?.provider?.name ?? t`your provider`);
        setLoading(false);
      })
      .catch((err) => {
        // Whatever the reason, there is no pending signup left to complete -
        // always show *something* rather than silently bouncing back to a
        // blank login page (the exact failure mode this page exists to fix).
        if (err?.response?.status === 403) {
          showLoginNotification({
            title: t`Registration Failed`,
            message: t`SSO registration is currently disabled.`,
            success: false
          });
        } else if (err?.response?.status === 409) {
          // No pending signup in the session - e.g. this page was loaded
          // directly, or the signup session has since expired.
          showLoginNotification({
            title: t`Registration Failed`,
            message: t`Your SSO sign-in session has expired. Please try logging in again.`,
            success: false
          });
        } else {
          showLoginNotification({
            title: t`Registration Failed`,
            message: t`An error occurred while completing SSO registration. Please try logging in again.`,
            success: false
          });
        }
        navigate('/login', { state: location?.state });
      });
  }, []);

  function handleSubmit() {
    setFormError(undefined);
    setSubmitting(true);

    api
      .post(apiUrl(ApiEndpoints.auth_provider_signup), form.values, {
        headers: { Authorization: '' }
      })
      .then((response) => {
        handleSuccessFullAuth(response, navigate, location);
      })
      .catch((err) => {
        setSubmitting(false);

        const errors = err.response?.data?.errors;
        if (Array.isArray(errors)) {
          for (const e of errors) {
            if (e.param && e.param in form.values) {
              form.setFieldError(e.param, e.message);
            } else {
              setFormError(e.message);
            }
          }
        } else {
          setFormError(t`Check your input and try again.`);
        }
      });
  }

  if (loading) {
    return <Wrapper titleText={t`Complete Your Registration`} loader />;
  }

  return (
    <Wrapper titleText={t`Complete Your Registration`} logOff>
      <form onSubmit={form.onSubmit(handleSubmit)}>
        <Stack gap={0}>
          <Text size='sm' c='dimmed' mb='md'>
            <Trans>
              You have signed in with {providerName}, but no matching account
              exists yet. Confirm your details below to create one.
            </Trans>
          </Text>
          {formError && (
            <Alert color='red' mb='md'>
              {formError}
            </Alert>
          )}
          <TextInput
            required
            label={t`Username`}
            aria-label='provider-signup-username'
            placeholder={t`Your username`}
            {...form.getInputProps('username')}
          />
          <TextInput
            label={t`Email`}
            aria-label='provider-signup-email'
            placeholder='email@example.org'
            {...form.getInputProps('email')}
          />
        </Stack>
        <Group justify='space-between' mt='xl'>
          <Button type='submit' disabled={submitting} fullWidth>
            <Trans>Complete Registration</Trans>
          </Button>
        </Group>
      </form>
    </Wrapper>
  );
}
