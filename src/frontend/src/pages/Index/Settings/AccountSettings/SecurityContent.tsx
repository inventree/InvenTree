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
import { useEffect, useMemo, useState } from 'react';

import { api, queryClient } from '../../../../App';
import { YesNoButton } from '../../../../components/buttons/YesNoButton';
import { PlaceholderPill } from '../../../../components/items/Placeholder';
import { ApiEndpoints } from '../../../../enums/ApiEndpoints';
import { ProviderLogin } from '../../../../functions/auth';
import { apiUrl, useServerApiState } from '../../../../states/ApiState';
import { useUserState } from '../../../../states/UserState';
import type { Provider, SecuritySetting } from '../../../../states/states';

export function SecurityContent() {
  const [auth_settings, sso_enabled, mfa_enabled] = useServerApiState(
    (state) => [state.auth_settings, state.sso_enabled, state.mfa_enabled]
  );

  return (
    <Stack>
      <Title order={5}>
        <Trans>Email</Trans>
      </Title>
      <EmailContent />
      <Title order={5}>
        <Trans>Single Sign On Accounts</Trans>
      </Title>
      {sso_enabled() ? (
        <SsoContent auth_settings={auth_settings} />
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
        <Trans>Multifactor</Trans>
      </Title>

      {mfa_enabled() ? (
        <MfaContent />
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
        <Trans>Token</Trans>
      </Title>
      <TokenContent />
    </Stack>
  );
}

function EmailContent() {
  const [value, setValue] = useState<string>('');
  const [newEmailValue, setNewEmailValue] = useState('');
  const [session] = useUserState((state) => [state.session]);
  const { isLoading, data, refetch } = useQuery({
    queryKey: ['emails'],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.user_emails), {
          headers: { 'X-Session-Token': session }
        })
        .then((res) => res.data.data)
  });

  function runServerAction(
    url: ApiEndpoints,
    action: 'post' | 'put' | 'delete' = 'post'
  ) {
    let act: any;
    switch (action) {
      case 'post':
        act = api.post;
        break;
      case 'put':
        act = api.put;
        break;
      case 'delete':
        act = api.delete;
        break;
    }
    act(
      apiUrl(url),
      { email: value },
      { headers: { 'X-Session-Token': session } }
    )
      .then(() => {
        refetch();
      })
      .catch((res: any) => console.log(res.data));
  }

  function addEmail() {
    api
      .post(
        apiUrl(ApiEndpoints.user_emails),
        {
          email: newEmailValue
        },
        { headers: { 'X-Session-Token': session } }
      )
      .then(() => {
        refetch();
      })
      .catch((res) => console.log(res.data));
  }

  function changePrimary() {
    api
      .post(
        apiUrl(ApiEndpoints.user_emails),
        {
          email: value,
          primary: true
        },
        { headers: { 'X-Session-Token': session } }
      )
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
          <Button onClick={() => changePrimary()}>
            <Trans>Make Primary</Trans>
          </Button>
          <Button
            onClick={() => runServerAction(ApiEndpoints.user_emails, 'put')}
          >
            <Trans>Re-send Verification</Trans>
          </Button>
          <Button
            onClick={() => runServerAction(ApiEndpoints.user_emails, 'delete')}
          >
            <Trans>Remove</Trans>
          </Button>
        </Group>
      </Grid.Col>
      <Grid.Col span={6}>
        <Button onClick={addEmail}>
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

function SsoContent({
  auth_settings
}: Readonly<{ auth_settings: SecuritySetting | undefined }>) {
  const [value, setValue] = useState<string>('');
  const [currentProviders, setCurrentProviders] = useState<Provider[]>();
  const { session } = useUserState.getState();
  const { isLoading, data } = useQuery({
    queryKey: ['sso-list'],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.user_sso), {
          headers: { 'X-Session-Token': session }
        })
        .then((res) => res.data.data)
  });

  useEffect(() => {
    if (auth_settings === undefined) return;
    if (data === undefined) return;

    const configuredProviders = data.map((item: any) => {
      return item.provider;
    });
    function isAlreadyInUse(value: any) {
      return !configuredProviders.includes(value.id);
    }

    // remove providers that are used currently
    const newData =
      auth_settings.socialaccount.providers.filter(isAlreadyInUse);
    setCurrentProviders(newData);
  }, [auth_settings, data]);

  function removeProvider() {
    api
      .delete(apiUrl(ApiEndpoints.user_sso), {
        headers: { 'X-Session-Token': session }
      })
      .then(() => {
        queryClient.removeQueries({
          queryKey: ['sso-list']
        });
      })
      .catch((res) => console.log(res.data));
  }

  /* renderer */
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
            <Trans>
              There are no social network accounts connected to this account.{' '}
            </Trans>
          </Alert>
        ) : (
          <Stack>
            <Radio.Group
              value={value}
              onChange={setValue}
              name='sso_accounts'
              label={t`You can sign in to your account using any of the following third party accounts`}
            >
              <Stack mt='xs'>
                {data.map((link: any) => (
                  <Radio
                    key={link.id}
                    value={String(link.id)}
                    label={link.provider}
                  />
                ))}
              </Stack>
            </Radio.Group>
            <Button onClick={removeProvider}>
              <Trans>Remove</Trans>
            </Button>
          </Stack>
        )}
      </Grid.Col>
      <Grid.Col span={6}>
        <Stack>
          <Text>Add SSO Account</Text>
          <Text>
            {currentProviders === undefined ? (
              <Trans>Loading</Trans>
            ) : (
              <Stack gap='xs'>
                {currentProviders.map((provider: any) => (
                  <ProviderButton key={provider.id} provider={provider} />
                ))}
              </Stack>
            )}
          </Text>
        </Stack>
      </Grid.Col>
    </Grid>
  );
}

function MfaContent() {
  return (
    <>
      MFA Details
      <PlaceholderPill />
    </>
  );
}

function TokenContent() {
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
    if (isLoading || data === undefined) return null;
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

  /* renderer */
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
