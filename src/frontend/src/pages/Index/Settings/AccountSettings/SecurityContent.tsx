import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import type { AuthConfig, AuthProvider } from '@lib/types/Auth';
import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  Accordion,
  ActionIcon,
  Alert,
  Badge,
  Button,
  Grid,
  Group,
  Loader,
  Radio,
  SimpleGrid,
  Stack,
  Table,
  Text,
  TextInput
} from '@mantine/core';
import { hideNotification, showNotification } from '@mantine/notifications';
import { ErrorBoundary } from '@sentry/react';
import {
  IconAlertCircle,
  IconAt,
  IconRefresh,
  IconX
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useMemo, useState } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { DefaultFallback } from '../../../../components/Boundary';
import { StylishText } from '../../../../components/items/StylishText';
import { ProviderLogin, authApi } from '../../../../functions/auth';
import { useServerApiState } from '../../../../states/ServerApiState';
import { useUserState } from '../../../../states/UserState';
import { ApiTokenTable } from '../../../../tables/settings/ApiTokenTable';
import MFASettings from './MFASettings';

export function SecurityContent() {
  const [auth_config, sso_enabled] = useServerApiState(
    useShallow((state) => [state.auth_config, state.sso_enabled])
  );

  const user = useUserState();

  const onError = useCallback(
    (error: unknown, componentStack: string | undefined, eventId: string) => {
      console.error(`ERR: Error rendering component: ${error}`);
    },
    []
  );

  return (
    <Stack>
      <Accordion multiple defaultValue={['email']}>
        <Accordion.Item value='email'>
          <Accordion.Control>
            <StylishText size='lg'>{t`Email Addresses`}</StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <EmailSection />
          </Accordion.Panel>
        </Accordion.Item>
        <Accordion.Item value='sso'>
          <Accordion.Control>
            <StylishText size='lg'>{t`Single Sign On`}</StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            {sso_enabled() ? (
              <ProviderSection auth_config={auth_config} />
            ) : (
              <Alert
                icon={<IconAlertCircle size='1rem' />}
                title={t`Not enabled`}
                color='yellow'
              >
                <Trans>Single Sign On is not enabled for this server </Trans>
              </Alert>
            )}
          </Accordion.Panel>
        </Accordion.Item>
        <Accordion.Item value='mfa'>
          <Accordion.Control>
            <StylishText size='lg'>{t`Multi-Factor Authentication`}</StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <MFASettings />
          </Accordion.Panel>
        </Accordion.Item>
        <Accordion.Item value='token'>
          <Accordion.Control>
            <StylishText size='lg'>{t`Access Tokens`}</StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <ErrorBoundary
              fallback={<DefaultFallback title={'API Table'} />}
              onError={onError}
            >
              <ApiTokenTable only_myself />
            </ErrorBoundary>
          </Accordion.Panel>
        </Accordion.Item>
        {user.isSuperuser() && (
          <Accordion.Item value='session'>
            <Accordion.Control>
              <StylishText size='lg'>{t`Session Information`}</StylishText>
            </Accordion.Control>
            <Accordion.Panel>
              <AuthContextSection />
            </Accordion.Panel>
          </Accordion.Item>
        )}
      </Accordion>
    </Stack>
  );
}

function AuthContextSection() {
  const [auth_context, setAuthContext] = useServerApiState(
    useShallow((state) => [state.auth_context, state.setAuthContext])
  );

  const fetchAuthContext = useCallback(() => {
    authApi(apiUrl(ApiEndpoints.auth_session)).then((resp) => {
      setAuthContext(resp.data.data);
    });
  }, [setAuthContext]);

  return (
    <Stack gap='xs'>
      <Group>
        <ActionIcon
          onClick={fetchAuthContext}
          variant='transparent'
          aria-label='refresh-auth-context'
        >
          <IconRefresh />
        </ActionIcon>
      </Group>

      <Table>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>{t`Timestamp`}</Table.Th>
            <Table.Th>{t`Method`}</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {auth_context?.methods?.map((method: any, index: number) => (
            <Table.Tr key={`auth-method-${index}`}>
              <Table.Td>{parseDate(method.at)}</Table.Td>
              <Table.Td>{method.method}</Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Stack>
  );
}

function EmailSection() {
  const [selectedEmail, setSelectedEmail] = useState<string>('');
  const [newEmailValue, setNewEmailValue] = useState('');
  const { isLoading, data, refetch } = useQuery({
    queryKey: ['emails'],
    queryFn: () =>
      authApi(apiUrl(ApiEndpoints.auth_email)).then((res) => res.data.data)
  });
  const emailAvailable = useMemo(() => {
    return data == undefined || data.length == 0;
  }, [data]);

  function runServerAction(
    action: 'patch' | 'post' | 'put' | 'delete' = 'post',
    data?: any
  ) {
    const vals: any = data || { email: selectedEmail };
    return authApi(apiUrl(ApiEndpoints.auth_email), undefined, action, vals)
      .then(() => {
        refetch();
      })
      .catch((err) => {
        hideNotification('email-error');

        showNotification({
          id: 'email-error',
          title: t`Error`,
          message: t`Error while updating email`,
          color: 'red'
        });
      });
  }

  if (isLoading) return <Loader />;

  return (
    <SimpleGrid cols={{ xs: 1, md: 2 }} spacing='sm'>
      {emailAvailable ? (
        <Stack gap='xs'>
          <Alert
            icon={<IconAlertCircle size='1rem' />}
            title={t`Not Configured`}
            color='yellow'
          >
            <Trans>Currently no email addresses are registered.</Trans>
          </Alert>
        </Stack>
      ) : (
        <Radio.Group
          value={selectedEmail}
          onChange={setSelectedEmail}
          name='email_accounts'
          label={t`The following email addresses are associated with your account:`}
        >
          <Stack mt='xs'>
            {data.map((email: any) => (
              <Radio
                key={email.email}
                value={String(email.email)}
                label={
                  <Group justify='space-apart'>
                    {email.email}
                    <Group justify='right'>
                      {email.primary && (
                        <Badge color='blue'>
                          <Trans>Primary</Trans>
                        </Badge>
                      )}
                      {email.verified ? (
                        <Badge color='green'>
                          <Trans>Verified</Trans>
                        </Badge>
                      ) : (
                        <Badge color='yellow'>
                          <Trans>Unverified</Trans>
                        </Badge>
                      )}
                    </Group>
                  </Group>
                }
              />
            ))}
            <Group>
              <Button
                onClick={() =>
                  runServerAction('patch', {
                    email: selectedEmail,
                    primary: true
                  })
                }
                disabled={!selectedEmail}
              >
                <Trans>Make Primary</Trans>
              </Button>
              <Button
                onClick={() => runServerAction('put')}
                disabled={!selectedEmail}
              >
                <Trans>Re-send Verification</Trans>
              </Button>
              <Button
                onClick={() => runServerAction('delete')}
                disabled={!selectedEmail}
                color='red'
              >
                <Trans>Remove</Trans>
              </Button>
            </Group>
          </Stack>
        </Radio.Group>
      )}
      <Stack>
        <StylishText size='md'>{t`Add Email Address`}</StylishText>
        <TextInput
          label={t`E-Mail`}
          placeholder={t`E-Mail address`}
          leftSection={<IconAt />}
          aria-label='email-address-input'
          value={newEmailValue}
          onChange={(event) => setNewEmailValue(event.currentTarget.value)}
        />
        <Button
          aria-label='email-address-submit'
          onClick={() =>
            runServerAction('post', { email: newEmailValue }).catch((err) => {
              if (err.status == 400) {
                showNotification({
                  title: t`Error while adding email`,
                  message: err.response.data.errors
                    .map((error: any) => error.message)
                    .join('\n'),
                  color: 'red',
                  icon: <IconX />
                });
              }
            })
          }
        >
          <Trans>Add Email</Trans>
        </Button>
      </Stack>
    </SimpleGrid>
  );
}

function ProviderButton({ provider }: Readonly<{ provider: AuthProvider }>) {
  return (
    <Button
      key={provider.id}
      variant='outline'
      onClick={() => ProviderLogin(provider, 'connect')}
    >
      <Group justify='space-between'>{provider.name}</Group>
    </Button>
  );
}

function ProviderSection({
  auth_config
}: Readonly<{ auth_config: AuthConfig | undefined }>) {
  const [value, setValue] = useState<string>('');
  const { isLoading, data, refetch } = useQuery({
    queryKey: ['provider-list'],
    queryFn: () =>
      authApi(apiUrl(ApiEndpoints.auth_providers))
        .then((res) => res?.data?.data ?? [])
        .catch(() => [])
  });

  const availableProviders = useMemo(() => {
    if (!auth_config || !data) return [];

    const configuredProviders = data.map((item: any) => item.provider.id);
    return auth_config.socialaccount.providers.filter(
      (provider: any) => !configuredProviders.includes(provider.id)
    );
  }, [auth_config, data]);

  function removeProvider() {
    const [uid, provider] = value.split('$');
    authApi(apiUrl(ApiEndpoints.auth_providers), undefined, 'delete', {
      provider,
      account: uid
    })
      .then(() => {
        refetch();
      })
      .catch((res) => console.log(res.data));
  }

  if (isLoading) return <Loader />;

  return (
    <Grid>
      <Grid.Col span={6}>
        {data.length == 0 ? (
          <Stack gap='xs'>
            <Alert
              icon={<IconAlertCircle size='1rem' />}
              title={t`Not Configured`}
              color='yellow'
            >
              <Trans>There are no providers connected to this account.</Trans>
            </Alert>
          </Stack>
        ) : (
          <Stack>
            <Radio.Group
              value={value}
              onChange={setValue}
              name='sso_accounts'
              label={t`You can sign in to your account using any of the following providers`}
            >
              <Stack mt='xs'>
                {data.map((link: any) => (
                  <Radio
                    key={link.uid}
                    value={[link.uid, link.provider.id].join('$')}
                    label={`${link.provider.name}: ${link.display}`}
                  />
                ))}
              </Stack>
            </Radio.Group>
            <Button onClick={removeProvider}>
              <Trans>Remove Provider Link</Trans>
            </Button>
          </Stack>
        )}
      </Grid.Col>
      <Grid.Col span={6}>
        <Stack>
          <Text>Add SSO Account</Text>
          {availableProviders === undefined ? (
            <Text>
              <Trans>Loading</Trans>
            </Text>
          ) : (
            <Stack gap='xs'>
              {availableProviders.map((provider: any) => (
                <ProviderButton key={provider.id} provider={provider} />
              ))}
            </Stack>
          )}
        </Stack>
      </Grid.Col>
    </Grid>
  );
}

export const parseDate = (date: number) =>
  date == null ? 'Never' : new Date(date * 1000).toLocaleString();
