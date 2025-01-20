import { Trans, t } from '@lingui/macro';
import {
  Alert,
  Badge,
  Button,
  Code,
  Grid,
  Group,
  Loader,
  Modal,
  Radio,
  Stack,
  Table,
  Text,
  TextInput,
  Title
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { showNotification } from '@mantine/notifications';
import { IconAlertCircle, IconAt, IconX } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { api } from '../../../../App';
import { QRCode } from '../../../../components/barcodes/QRCode';
import { YesNoButton } from '../../../../components/buttons/YesNoButton';
import { ApiEndpoints } from '../../../../enums/ApiEndpoints';
import { ProviderLogin, authApi } from '../../../../functions/auth';
import { apiUrl, useServerApiState } from '../../../../states/ApiState';
import type { AuthConfig, Provider } from '../../../../states/states';
import { useReauth } from './useConfirm';

export function SecurityContent() {
  const [auth_config, sso_enabled] = useServerApiState((state) => [
    state.auth_config,
    state.sso_enabled
  ]);

  return (
    <Stack>
      <Title order={5}>
        <Trans>Email Addresses</Trans>
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
      <MfaSection />
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
            <Trans>Currently no email adreesses are registered</Trans>
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
  const [getReauthText, ReauthModal] = useReauth();
  const [recoveryCodes, setRecoveryCodes] = useState<
    Recoverycodes | undefined
  >();
  const [
    recoveryCodesOpen,
    { open: openRecoveryCodes, close: closeRecoveryCodes }
  ] = useDisclosure(false);
  const { isLoading, data, refetch } = useQuery({
    queryKey: ['mfa-list'],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.auth_authenticators))
        .then((res) => res.data.data)
  });

  function showRecoveryCodes(codes: Recoverycodes) {
    setRecoveryCodes(codes);
    openRecoveryCodes();
  }

  const removeTotp = () => {
    runActionWithFallback(
      () =>
        authApi(apiUrl(ApiEndpoints.auth_totp), undefined, 'delete').then(
          () => {
            refetch();
            return ResultType.success;
          }
        ),
      getReauthText
    );
  };
  const viewRecoveryCodes = () => {
    runActionWithFallback(
      () =>
        authApi(apiUrl(ApiEndpoints.auth_recovery), undefined, 'get').then(
          (res) => {
            showRecoveryCodes(res.data.data);
            return ResultType.success;
          }
        ),
      getReauthText
    );
  };

  const parseDate = (date: number) =>
    date == null ? 'Never' : new Date(date * 1000).toLocaleString();

  const rows = useMemo(() => {
    if (isLoading || !data) return null;
    return data.map((token: any) => (
      <Table.Tr key={`${token.created_at}-${token.type}`}>
        <Table.Td>{token.type}</Table.Td>
        <Table.Td>{parseDate(token.last_used_at)}</Table.Td>
        <Table.Td>{parseDate(token.created_at)}</Table.Td>
        <Table.Td>
          {token.type == 'totp' && (
            <Button color='red' onClick={removeTotp}>
              <Trans>Remove</Trans>
            </Button>
          )}
          {token.type == 'recovery_codes' && (
            <Button onClick={viewRecoveryCodes}>
              <Trans>View</Trans>
            </Button>
          )}
        </Table.Td>
      </Table.Tr>
    ));
  }, [data, isLoading]);

  const usedFactors: string[] = useMemo(() => {
    if (isLoading || !data) return [];
    return data.map((token: any) => token.type);
  }, [data]);

  if (isLoading) return <Loader />;

  return (
    <>
      <ReauthModal />
      <Grid>
        <Grid.Col span={6}>
          {data.length == 0 ? (
            <Alert icon={<IconAlertCircle size='1rem' />} color='yellow'>
              <Trans>No factors configured</Trans>
            </Alert>
          ) : (
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
                  <Table.Th>
                    <Trans>Actions</Trans>
                  </Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>{rows}</Table.Tbody>
            </Table>
          )}
        </Grid.Col>
        <Grid.Col span={6}>
          <MfaAddSection
            usedFactors={usedFactors}
            refetch={refetch}
            showRecoveryCodes={showRecoveryCodes}
          />
          <Modal
            opened={recoveryCodesOpen}
            onClose={() => {
              refetch();
              closeRecoveryCodes();
            }}
            title={t`Recovery Codes`}
            centered
          >
            <Title order={3}>
              <Trans>Unused Codes</Trans>
            </Title>
            <Code>{recoveryCodes?.unused_codes?.join('\n')}</Code>

            <Title order={3}>
              <Trans>Used Codes</Trans>
            </Title>
            <Code>{recoveryCodes?.used_codes?.join('\n')}</Code>
          </Modal>
        </Grid.Col>
      </Grid>
    </>
  );
}

enum ResultType {
  success = 0,
  reauth = 1,
  mfareauth = 2,
  error = 3
}

export interface Recoverycodes {
  type: string;
  created_at: number;
  last_used_at: null;
  total_code_count: number;
  unused_code_count: number;
  unused_codes: string[];
  used_code_count: number;
  used_codes: string[];
}

function MfaAddSection({
  usedFactors,
  refetch,
  showRecoveryCodes
}: Readonly<{
  usedFactors: string[];
  refetch: () => void;
  showRecoveryCodes: (codes: Recoverycodes) => void;
}>) {
  const [auth_config] = useServerApiState((state) => [state.auth_config]);
  const [totpQrOpen, { open: openTotpQr, close: closeTotpQr }] =
    useDisclosure(false);
  const [totpQr, setTotpQr] = useState<{ totp_url: string; secret: string }>();
  const [value, setValue] = useState('');
  const [getReauthText, ReauthModal] = useReauth();

  const registerRecoveryCodes = async () => {
    await runActionWithFallback(
      () =>
        authApi(apiUrl(ApiEndpoints.auth_recovery), undefined, 'post')
          .then((res) => {
            showRecoveryCodes(res.data.data);
            return ResultType.success;
          })
          .catch((err) => {
            showNotification({
              title: t`Error while registering recovery codes`,
              message: err.response.data.errors
                .map((error: any) => error.message)
                .join('\n'),
              color: 'red',
              icon: <IconX />
            });

            return ResultType.error;
          }),
      getReauthText
    );
  };
  const registerTotp = async () => {
    await runActionWithFallback(
      () =>
        authApi(apiUrl(ApiEndpoints.auth_totp), undefined, 'get')
          .then(() => ResultType.error)
          .catch((err) => {
            if (err.status == 404 && err.response.data.meta.secret) {
              setTotpQr(err.response.data.meta);
              openTotpQr();
              return ResultType.success;
            }
            return ResultType.error;
          }),
      getReauthText
    );
  };

  const possibleFactors = useMemo(() => {
    return [
      {
        type: 'totp',
        name: t`TOTP`,
        description: t`Time-based One-Time Password`,
        function: registerTotp,
        used: usedFactors?.includes('totp')
      },
      {
        type: 'recovery_codes',
        name: t`Recovery Codes`,
        description: t`One-Time pre-generated recovery codes`,
        function: registerRecoveryCodes,
        used: usedFactors?.includes('recovery_codes')
      }
    ].filter((factor) => {
      auth_config?.mfa.supported_types.includes(factor.type);
    });
  }, [usedFactors, auth_config]);

  return (
    <Stack>
      <ReauthModal />
      <Text>Add Factor</Text>
      {possibleFactors.map((factor) => (
        <Button
          key={factor.type}
          onClick={factor.function}
          disabled={factor.used}
          variant='outline'
        >
          {factor.name}
        </Button>
      ))}
      <Modal
        opened={totpQrOpen}
        onClose={closeTotpQr}
        title={t`Register TOTP token`}
      >
        <Stack>
          <QRCode data={totpQr?.totp_url} />
          <Text>
            <Trans>Secret</Trans>
            <br />
            {totpQr?.secret}
          </Text>
          <TextInput
            required
            label={t`One-Time Password`}
            description={t`Enter the TOTP code to ensure it registered correctly`}
            value={value}
            onChange={(event) => setValue(event.currentTarget.value)}
          />
          <Button
            fullWidth
            onClick={() =>
              runActionWithFallback(
                () =>
                  authApi(apiUrl(ApiEndpoints.auth_totp), undefined, 'post', {
                    code: value
                  }).then(() => {
                    closeTotpQr();
                    refetch();
                    return ResultType.success;
                  }),
                getReauthText
              )
            }
          >
            <Trans>Submit</Trans>
          </Button>
        </Stack>
      </Modal>
    </Stack>
  );
}

async function runActionWithFallback(
  action: () => Promise<ResultType>,
  getReauthText: (props: any) => any
) {
  const { setAuthContext } = useServerApiState.getState();
  const rslt = await action().catch((err) => {
    setAuthContext(err.response.data?.data);
    // check if we need to re-authenticate
    if (err.status == 401) {
      if (
        err.response.data.data.flows.find(
          (flow: any) => flow.id == 'mfa_reauthenticate'
        )
      ) {
        return ResultType.mfareauth;
      } else if (
        err.response.data.data.flows.find(
          (flow: any) => flow.id == 'reauthenticate'
        )
      ) {
        return ResultType.reauth;
      } else {
        return ResultType.error;
      }
    } else {
      return ResultType.error;
    }
  });
  if (rslt == ResultType.mfareauth) {
    authApi(apiUrl(ApiEndpoints.auth_mfa_reauthenticate), undefined, 'post', {
      code: await getReauthText({
        label: t`TOTP Code`,
        name: 'TOTP',
        description: t`Enter your TOTP or recovery code`
      })
    })
      .then((response) => {
        setAuthContext(response.data?.data);
        action();
      })
      .catch((err) => {
        setAuthContext(err.response.data?.data);
      });
  } else if (rslt == ResultType.reauth) {
    authApi(apiUrl(ApiEndpoints.auth_reauthenticate), undefined, 'post', {
      password: await getReauthText({
        label: t`Password`,
        name: 'password',
        description: t`Enter your password`
      })
    })
      .then((response) => {
        setAuthContext(response.data?.data);
        action();
      })
      .catch((err) => {
        setAuthContext(err.response.data?.data);
      });
  }
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
