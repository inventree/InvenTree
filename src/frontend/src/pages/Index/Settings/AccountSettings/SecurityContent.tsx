import { Trans, t } from '@lingui/macro';
import {
  Alert,
  Badge,
  Button,
  Grid,
  Group,
  Loader,
  Radio,
  Stack,
  Table,
  Text,
  TextInput,
  Title
} from '@mantine/core';
import { IconAlertCircle, IconAt } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';

import { api } from '../../../../App';
import { YesNoButton } from '../../../../components/buttons/YesNoButton';
import { ApiEndpoints } from '../../../../enums/ApiEndpoints';
import { ProviderLogin, authApi } from '../../../../functions/auth';
import { apiUrl, useServerApiState } from '../../../../states/ApiState';
import type { AuthConfig, Provider } from '../../../../states/states';

export function SecurityContent() {
  const [auth_config, sso_enabled, mfa_enabled] = useServerApiState((state) => [
    state.auth_config,
    state.sso_enabled,
    state.mfa_enabled
  ]);

  return (
    <Stack>
      <Title order={5}>
        <Trans>Email</Trans>
      </Title>
      <EmailSection />
      <Title order={5}>
        <Trans>Single Sign On</Trans>
      </Title>
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
      <Title order={5}>
        <Trans>Multifactor authentication</Trans>
      </Title>
      {mfa_enabled() ? (
        <MfaSection />
      ) : (
        <Alert
          icon={<IconAlertCircle size='1rem' />}
          title={t`Not enabled`}
          color='yellow'
        >
          <Trans>
            Multifactor authentication is not configured for your account{' '}
          </Trans>
        </Alert>
      )}
      <Title order={5}>
        <Trans>Access Tokens</Trans>
      </Title>
      <TokenSection />
    </Stack>
  );
}

function EmailSection() {
  const [value, setValue] = useState<string>('');
  const [newEmailValue, setNewEmailValue] = useState('');
  const { isLoading, data, refetch } = useQuery({
    queryKey: ['emails'],
    queryFn: () =>
      authApi(apiUrl(ApiEndpoints.auth_email)).then((res) => res.data.data)
  });

  function runServerAction(
    action: 'post' | 'put' | 'delete' = 'post',
    data?: any
  ) {
    const vals: any = data || { email: value };
    authApi(apiUrl(ApiEndpoints.auth_email), undefined, action, vals)
      .then(() => {
        refetch();
      })
      .catch((res: any) => console.log(res.data));
  }

  if (isLoading) return <Loader />;

  return (
    <Grid>
      <Grid.Col span={6}>
        {data.length == 0 ? (
          <Text>
            <Trans>Currently no emails are registered</Trans>
          </Text>
        ) : (
          <Radio.Group
            value={value}
            onChange={setValue}
            name='email_accounts'
            label={t`The following email addresses are associated with your account:`}
          >
            <Stack mt='xs'>
              {data.map((email: any) => (
                <Radio
                  key={email.email}
                  value={String(email.email)}
                  label={
                    <Group justify='space-between'>
                      {email.email}
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
                  }
                />
              ))}
            </Stack>
          </Radio.Group>
        )}
      </Grid.Col>
      <Grid.Col span={6}>
        <Stack>
          <Text>
            <Trans>Add Email Address</Trans>
          </Text>
          <TextInput
            label={t`E-Mail`}
            placeholder={t`E-Mail address`}
            leftSection={<IconAt />}
            value={newEmailValue}
            onChange={(event) => setNewEmailValue(event.currentTarget.value)}
          />
        </Stack>
      </Grid.Col>
      <Grid.Col span={6}>
        <Group>
          <Button
            onClick={() =>
              runServerAction('post', { email: value, primary: true })
            }
          >
            <Trans>Make Primary</Trans>
          </Button>
          <Button onClick={() => runServerAction('put')}>
            <Trans>Re-send Verification</Trans>
          </Button>
          <Button onClick={() => runServerAction('delete')}>
            <Trans>Remove</Trans>
          </Button>
        </Group>
      </Grid.Col>
      <Grid.Col span={6}>
        <Button
          onClick={() => runServerAction('post', { email: newEmailValue })}
        >
          <Trans>Add Email</Trans>
        </Button>
      </Grid.Col>
    </Grid>
  );
}

function ProviderButton({ provider }: Readonly<{ provider: Provider }>) {
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
      authApi(apiUrl(ApiEndpoints.auth_providers)).then((res) => res.data.data)
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
          <Alert
            icon={<IconAlertCircle size='1rem' />}
            title={t`Not configured`}
            color='yellow'
          >
            <Trans>There are no providers connected to this account. </Trans>
          </Alert>
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

function MfaSection() {
  const { isLoading, data } = useQuery({
    queryKey: ['mfa-list'],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.auth_authenticators))
        .then((res) => res.data.data)
  });

  const parseDate = (date: number) =>
    date == null ? 'Never' : new Date(date * 1000).toLocaleString();

  const rows = useMemo(() => {
    if (isLoading || !data) return null;
    return data.map((token: any) => (
      <Table.Tr key={`${token.created_at}-${token.type}`}>
        <Table.Td>{token.type}</Table.Td>
        <Table.Td>{parseDate(token.last_used_at)}</Table.Td>
        <Table.Td>{parseDate(token.created_at)}</Table.Td>
      </Table.Tr>
    ));
  }, [data, isLoading]);

  if (isLoading) return <Loader />;

  if (data.length == 0)
    return (
      <Alert icon={<IconAlertCircle size='1rem' />} color='green'>
        <Trans>No factors configured</Trans>
      </Alert>
    );

  return (
    <Table stickyHeader striped highlightOnHover withTableBorder>
      <Table.Thead>
        <Table.Tr>
          <Table.Th>
            <Trans>Type</Trans>
          </Table.Th>
          <Table.Th>
            <Trans>Last used at</Trans>
          </Table.Th>
          <Table.Th>
            <Trans>Created at</Trans>
          </Table.Th>
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>{rows}</Table.Tbody>
    </Table>
  );
}

function TokenSection() {
  const { isLoading, data, refetch } = useQuery({
    queryKey: ['token-list'],
    queryFn: () =>
      api.get(apiUrl(ApiEndpoints.user_tokens)).then((res) => res.data)
  });

  function revokeToken(id: string) {
    api
      .delete(apiUrl(ApiEndpoints.user_tokens, id))
      .then(() => {
        refetch();
      })
      .catch((res) => console.log(res.data));
  }

  const rows = useMemo(() => {
    if (isLoading || !data) return null;
    return data.map((token: any) => (
      <Table.Tr key={token.id}>
        <Table.Td>
          <YesNoButton value={token.active} />
        </Table.Td>
        <Table.Td>{token.expiry}</Table.Td>
        <Table.Td>{token.last_seen}</Table.Td>
        <Table.Td>{token.token}</Table.Td>
        <Table.Td>{token.name}</Table.Td>
        <Table.Td>
          {token.in_use ? (
            <Trans>Token is used - no actions</Trans>
          ) : (
            <Button
              onClick={() => revokeToken(token.id)}
              color='red'
              disabled={!token.active}
            >
              <Trans>Revoke</Trans>
            </Button>
          )}
        </Table.Td>
      </Table.Tr>
    ));
  }, [data, isLoading]);

  if (isLoading) return <Loader />;

  if (data.length == 0)
    return (
      <Alert icon={<IconAlertCircle size='1rem' />} color='green'>
        <Trans>No tokens configured</Trans>
      </Alert>
    );

  return (
    <Table stickyHeader striped highlightOnHover withTableBorder>
      <Table.Thead>
        <Table.Tr>
          <Table.Th>
            <Trans>Active</Trans>
          </Table.Th>
          <Table.Th>
            <Trans>Expiry</Trans>
          </Table.Th>
          <Table.Th>
            <Trans>Last Seen</Trans>
          </Table.Th>
          <Table.Th>
            <Trans>Token</Trans>
          </Table.Th>
          <Table.Th>
            <Trans>Name</Trans>
          </Table.Th>
          <Table.Th>
            <Trans>Actions</Trans>
          </Table.Th>
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>{rows}</Table.Tbody>
    </Table>
  );
}
