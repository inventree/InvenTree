import { Trans, t } from '@lingui/macro';
import {
  Accordion,
  Alert,
  Badge,
  Button,
  Code,
  Grid,
  Group,
  Loader,
  Modal,
  Radio,
  SimpleGrid,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
  Tooltip
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { hideNotification, showNotification } from '@mantine/notifications';
import {
  IconAlertCircle,
  IconAt,
  IconCircleX,
  IconExclamationCircle,
  IconX
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useMemo, useState } from 'react';
import { api } from '../../../../App';
import { StylishText } from '../../../../components/items/StylishText';
import { ApiEndpoints } from '../../../../enums/ApiEndpoints';
import { ProviderLogin, authApi } from '../../../../functions/auth';
import { showApiErrorMessage } from '../../../../functions/notifications';
import { useTable } from '../../../../hooks/UseTable';
import { apiUrl, useServerApiState } from '../../../../states/ApiState';
import type { AuthConfig, Provider } from '../../../../states/states';
import { BooleanColumn } from '../../../../tables/ColumnRenderers';
import { InvenTreeTable } from '../../../../tables/InvenTreeTable';
import type { RowAction } from '../../../../tables/RowActions';
import { QrRegistrationForm } from './QrRegistrationForm';
import { useReauth } from './useConfirm';

export function SecurityContent() {
  const [auth_config, sso_enabled] = useServerApiState((state) => [
    state.auth_config,
    state.sso_enabled
  ]);

  return (
    <Stack>
      <Accordion multiple defaultValue={['email', 'sso', 'mfa', 'token']}>
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
            <MfaSection />
          </Accordion.Panel>
        </Accordion.Item>
        <Accordion.Item value='token'>
          <Accordion.Control>
            <StylishText size='lg'>{t`Access Tokens`}</StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <TokenSection />
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>
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
        <Alert
          icon={<IconAlertCircle size='1rem' />}
          title={t`Not Configured`}
          color='yellow'
        >
          <Trans>Currently no email addresses are registered.</Trans>
        </Alert>
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
            title={t`Not Configured`}
            color='yellow'
          >
            <Trans>There are no providers connected to this account.</Trans>
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
      <SimpleGrid cols={{ xs: 1, md: 2 }} spacing='sm'>
        {data.length == 0 ? (
          <Alert
            title={t`Not Configured`}
            icon={<IconAlertCircle size='1rem' />}
            color='yellow'
          >
            <Trans>No multi-factor tokens configured for this account</Trans>
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
      </SimpleGrid>
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
      return auth_config?.mfa?.supported_types.includes(factor.type);
    });
  }, [usedFactors, auth_config]);

  const [totpError, setTotpError] = useState<string>('');

  return (
    <Stack>
      <ReauthModal />
      <StylishText size='md'>{t`Add Token`}</StylishText>
      {possibleFactors.map((factor) => (
        <Tooltip label={factor.description} key={factor.type}>
          <Button
            onClick={factor.function}
            disabled={factor.used}
            variant='outline'
          >
            {factor.name}
          </Button>
        </Tooltip>
      ))}
      <Modal
        opened={totpQrOpen}
        onClose={closeTotpQr}
        title={<StylishText size='lg'>{t`Register TOTP Token`}</StylishText>}
      >
        <Stack>
          <QrRegistrationForm
            url={totpQr?.totp_url ?? ''}
            secret={totpQr?.secret ?? ''}
            value={value}
            error={totpError}
            setValue={setValue}
          />
          <Button
            fullWidth
            onClick={() =>
              runActionWithFallback(
                () =>
                  authApi(apiUrl(ApiEndpoints.auth_totp), undefined, 'post', {
                    code: value
                  })
                    .then(() => {
                      setTotpError('');
                      closeTotpQr();
                      refetch();
                      return ResultType.success;
                    })
                    .catch((error) => {
                      const errorMsg = t`Error registering TOTP token`;

                      setTotpError(
                        error.response?.data?.errors[0]?.message ?? errorMsg
                      );

                      hideNotification('totp-error');
                      showNotification({
                        id: 'totp-error',
                        title: t`Error`,
                        message: errorMsg,
                        color: 'red',
                        icon: <IconExclamationCircle />
                      });
                      return ResultType.error;
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
  const table = useTable('api-tokens', 'id');

  const tableColumns = useMemo(() => {
    return [
      {
        accessor: 'name'
      },
      BooleanColumn({
        accessor: 'active'
      }),
      {
        accessor: 'token'
      },
      {
        accessor: 'last_seen'
      },
      {
        accessor: 'expiry'
      }
    ];
  }, []);

  const rowActions = useCallback((record: any): RowAction[] => {
    return [
      {
        title: t`Revoke`,
        color: 'red',
        hidden: !record.active || record.in_use,
        icon: <IconCircleX />,
        onClick: () => {
          revokeToken(record.id);
        }
      }
    ];
  }, []);

  const revokeToken = async (id: string) => {
    api
      .delete(apiUrl(ApiEndpoints.user_tokens, id))
      .then(() => {
        table.refreshTable();
      })
      .catch((error) => {
        showApiErrorMessage({
          error: error,
          title: t`Error revoking token`
        });
      });
  };

  return (
    <InvenTreeTable
      tableState={table}
      url={apiUrl(ApiEndpoints.user_tokens)}
      columns={tableColumns}
      props={{
        rowActions: rowActions,
        enableSearch: false,
        enableColumnSwitching: false
      }}
    />
  );
}
