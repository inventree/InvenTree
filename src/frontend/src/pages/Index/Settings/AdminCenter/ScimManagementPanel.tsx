import { CopyButton } from '@lib/components/CopyButton';
import { RowDeleteAction, RowEditAction } from '@lib/components/RowActions';
import type { RowAction } from '@lib/components/RowActions';
import { StylishText } from '@lib/components/StylishText';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { navigateToLink } from '@lib/functions/Navigation';
import useTable from '@lib/hooks/UseTable';
import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  Accordion,
  Alert,
  Anchor,
  Badge,
  Button,
  Code,
  Divider,
  Group,
  Loader,
  Modal,
  Paper,
  SimpleGrid,
  Stack,
  Table,
  Text
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { showNotification } from '@mantine/notifications';
import {
  IconArrowBigLeft,
  IconArrowBigRight,
  IconPlus,
  IconShieldLock,
  IconShieldOff
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, queryClient } from '../../../../App';
import { GlobalSettingList } from '../../../../components/settings/SettingList';
import { InvenTreeTable } from '../../../../components/tables/InvenTreeTable';
import { showApiErrorMessage } from '../../../../functions/notifications';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../../../hooks/UseForm';
import { useLocalState } from '../../../../states/LocalState';

export function ScimManagementPanel() {
  const [secret, setSecret] = useState<string>('');
  const [
    secretModalOpened,
    { open: openSecretModal, close: closeSecretModal }
  ] = useDisclosure(false);

  const { data, isFetching } = useQuery({
    queryKey: ['scim-config'],
    queryFn: () =>
      api.get(apiUrl(ApiEndpoints.scim_config)).then((res) => res.data),
    refetchOnMount: true
  });

  const generateSecret = (action: 'generate' | 'rotate') => {
    api
      .post(apiUrl(ApiEndpoints.scim_generate))
      .then((res) => {
        setSecret(res.data.secret);
        openSecretModal();
        queryClient.invalidateQueries({ queryKey: ['scim-config'] });
        showNotification({
          title:
            action === 'generate' ? t`SCIM enabled` : t`SCIM secret rotated`,
          message: t`The new bearer secret is only shown once`,
          color: 'green'
        });
      })
      .catch((error) => {
        showApiErrorMessage({ error, title: t`Error generating SCIM secret` });
      });
  };

  const disableScim = () => {
    api
      .post(apiUrl(ApiEndpoints.scim_disable))
      .then(() => {
        queryClient.invalidateQueries({ queryKey: ['scim-config'] });
        showNotification({
          title: t`SCIM disabled`,
          message: t`The SCIM provisioning endpoint has been disabled and its secret revoked`,
          color: 'blue'
        });
      })
      .catch((error) => {
        showApiErrorMessage({ error, title: t`Error disabling SCIM` });
      });
  };

  if (isFetching && !data) {
    return <Loader />;
  }

  return (
    <Stack gap='md'>
      <Modal
        opened={secretModalOpened}
        onClose={closeSecretModal}
        title={<StylishText size='xl'>{t`SCIM Bearer Secret`}</StylishText>}
        centered
        data-testid='scim-secret-modal'
      >
        <Alert color='yellow' mb='sm'>
          <Trans>
            This secret is only shown once - copy it now and store it in your
            Identity Provider's SCIM configuration. It cannot be retrieved
            again, only rotated.
          </Trans>
        </Alert>
        <Paper p='sm' withBorder>
          <Group justify='space-between' wrap='nowrap'>
            <Code style={{ wordBreak: 'break-all', whiteSpace: 'normal' }}>
              {secret}
            </Code>
            <CopyButton value={secret} />
          </Group>
        </Paper>
      </Modal>

      <Alert icon={<IconShieldLock />} color='blue'>
        <Trans>
          SCIM allows an external Identity Provider (e.g. Okta, Microsoft Entra
          ID, OneLogin) to automatically provision and deprovision Users and
          Groups. Single Sign-On (interactive login) is configured separately,
          under Single Sign On.
        </Trans>
      </Alert>

      <Table>
        <Table.Tbody>
          <Table.Tr>
            <Table.Td>
              <Trans>Status</Trans>
            </Table.Td>
            <Table.Td>
              {data?.enabled ? (
                <Badge color='green'>
                  <Trans>Enabled</Trans>
                </Badge>
              ) : (
                <Badge color='gray'>
                  <Trans>Disabled</Trans>
                </Badge>
              )}
            </Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Td>
              <Trans>Base URL</Trans>
            </Table.Td>
            <Table.Td>
              <Group gap='xs' wrap='nowrap'>
                <Code>{data?.base_url}</Code>
                <CopyButton value={data?.base_url} />
              </Group>
            </Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Td>
              <Trans>Secret Generated</Trans>
            </Table.Td>
            <Table.Td>{data?.secret_generated ?? '-'}</Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Td>
              <Trans>Last Used</Trans>
            </Table.Td>
            <Table.Td>{data?.last_used ?? '-'}</Table.Td>
          </Table.Tr>
        </Table.Tbody>
      </Table>

      <Divider />

      <Group>
        <Button
          leftSection={<IconShieldLock size={16} />}
          onClick={() => generateSecret(data?.enabled ? 'rotate' : 'generate')}
        >
          {data?.enabled ? (
            <Trans>Rotate Secret</Trans>
          ) : (
            <Trans>Enable SCIM</Trans>
          )}
        </Button>
        {data?.enabled && (
          <Button
            color='red'
            variant='outline'
            leftSection={<IconShieldOff size={16} />}
            onClick={disableScim}
          >
            <Trans>Disable SCIM</Trans>
          </Button>
        )}
      </Group>

      <Text size='sm' c='dimmed'>
        <Trans>
          Rotating the secret immediately invalidates the previous one - update
          your Identity Provider's configuration straight away.
        </Trans>
      </Text>
    </Stack>
  );
}

function SSOManagementPanel() {
  const navigate = useNavigate();
  const { getHost } = useLocalState();
  const table = useTable('sso-applications', { idAccessor: 'id' });
  const [oidcCallback, setOidcCallback] = useState<string | null>(null);
  const [selectedSsoApplication, setSelectedSsoApplication] = useState<
    number | undefined
  >(undefined);

  const newGenericSsoApplication = useCreateApiFormModal({
    url: ApiEndpoints.sso_list,
    title: t`Add SSO Application`,
    table: table,
    fields: {
      name: {},
      provider: {},
      provider_id: {},
      client_id: {},
      secret: {},
      settings: {}
    }
  });

  const newOidcSsoApplication = useCreateApiFormModal({
    url: ApiEndpoints.sso_list,
    title: t`Add OIDC SSO Application`,
    table: table,
    fields: {
      provider: {
        hidden: true,
        value: 'openid_connect'
      },
      name: {},
      provider_id: { required: true },
      client_id: {},
      secret: { required: true },
      oauth_pkce_enabled: {
        field_type: 'boolean',
        label: t`OAuth PKCE Enabled`,
        description: t`Use Proof Key for Code Exchange during OIDC login with this application`,
        default: true
      },
      server_url: {
        field_type: 'string',
        label: t`OIDC Server URL`,
        description: t`Base URL of the OIDC provider`
      },
      uid_field: {
        field_type: 'string',
        label: t`UID Field`,
        description: t`OIDC claim used as the user's unique identifier`,
        default: 'sub'
      }
    },
    processFormData: (data) => {
      const { oauth_pkce_enabled, server_url, uid_field, ...applicationData } =
        data;

      return {
        ...applicationData,
        settings: {
          oauth_pkce_enabled,
          server_url,
          uid_field
        }
      };
    },
    onFormSuccess: (data) => {
      setOidcCallback(
        new URL(
          `/accounts/oidc/${data.provider_id}/login/callback/`,
          getHost()
        ).toString()
      );
    }
  });

  const editSsoApplication = useEditApiFormModal({
    url: ApiEndpoints.sso_list,
    pk: selectedSsoApplication,
    title: t`Edit SSO Application`,
    table: table,
    fields: {
      name: {},
      provider: {},
      provider_id: {},
      client_id: {},
      secret: {},
      settings: {}
    }
  });

  const deleteSsoApplication = useDeleteApiFormModal({
    url: ApiEndpoints.sso_list,
    pk: selectedSsoApplication,
    title: t`Delete SSO Application`,
    table: table
  });

  const ssoColumns = useMemo(
    () => [
      {
        accessor: 'name',
        title: t`Name`,
        sortable: true,
        switchable: false
      },
      {
        accessor: 'provider',
        title: t`Provider`,
        sortable: true,
        switchable: true
      },
      {
        accessor: 'provider_id',
        title: t`Provider ID`,
        sortable: true,
        switchable: true
      },
      {
        accessor: 'client_id',
        title: t`Client ID`,
        sortable: true,
        switchable: true
      }
    ],
    []
  );

  const rowActions = useCallback(
    (record: any): RowAction[] => [
      RowEditAction({
        onClick: () => {
          setSelectedSsoApplication(record.id);
          editSsoApplication.open();
        }
      }),
      RowDeleteAction({
        onClick: () => {
          setSelectedSsoApplication(record.id);
          deleteSsoApplication.open();
        }
      })
    ],
    [deleteSsoApplication, editSsoApplication]
  );

  const tableActions = useMemo(
    () => [
      <Button
        key={'add-generic-sso-application'}
        leftSection={<IconPlus size={16} />}
        onClick={() => newGenericSsoApplication.open()}
      >
        <Trans>Add Generic App</Trans>
      </Button>,
      <Button
        key={'add-oidc-sso-application'}
        leftSection={<IconPlus size={16} />}
        onClick={() => newOidcSsoApplication.open()}
      >
        <Trans>Add OIDC App</Trans>
      </Button>
    ],
    [newGenericSsoApplication, newOidcSsoApplication]
  );

  return (
    <Stack gap='md'>
      <Text>
        <Trans>
          Frontend Single Sign-On (SSO) is based on django-allauth. By default
          generic OIDC (client) and SAML providers are enabled.
          <br />
          You can add more specific providers using the
          `INVENTREE_SOCIAL_BACKENDS` config key. After a restart those
          providers become available below.
          <br />
          The documentation goes more in depth on SSO setup steps.
        </Trans>
      </Text>
      {newGenericSsoApplication.modal}
      <Modal
        opened={oidcCallback !== null}
        onClose={() => setOidcCallback(null)}
        title={<StylishText size='xl'>{t`OIDC Callback URL`}</StylishText>}
        centered
      >
        <Stack gap='sm'>
          <Text>{t`Add this callback URL to your OIDC provider.`}</Text>
          <Group justify='space-between' wrap='nowrap'>
            <Code style={{ wordBreak: 'break-all', whiteSpace: 'normal' }}>
              {oidcCallback}
            </Code>
            <CopyButton value={oidcCallback ?? ''} />
          </Group>
        </Stack>
      </Modal>
      {newOidcSsoApplication.modal}
      {editSsoApplication.modal}
      {deleteSsoApplication.modal}
      <InvenTreeTable
        tableState={table}
        url={apiUrl(ApiEndpoints.sso_list)}
        columns={ssoColumns}
        props={{
          enableSearch: true,
          enableColumnSwitching: true,
          enableSelection: false,
          enablePagination: true,
          enableRefresh: true,
          rowActions: rowActions,
          tableActions: tableActions
        }}
      />
      <GlobalSettingList
        heading={t`Single Sign-On (SSO) Settings`}
        keys={[
          'LOGIN_ENABLE_SSO',
          'LOGIN_ENABLE_SSO_REG',
          'LOGIN_SIGNUP_SSO_AUTO'
        ]}
      />
      <Alert color='blue'>
        <Trans>
          More settings can be found in the{' '}
          <Anchor
            onClick={(event: any) =>
              navigateToLink('/settings/system/authentication', navigate, event)
            }
            style={{ textDecoration: 'underline' }}
          >
            system settings
          </Anchor>
          .
        </Trans>
      </Alert>
    </Stack>
  );
}

function headerSection(text: string, out = false) {
  return (
    <Group>
      {out ? <IconArrowBigLeft size={16} /> : <IconArrowBigRight size={16} />}
      <StylishText size='lg'>{text}</StylishText>
    </Group>
  );
}

export default function IdentityManagementPanel() {
  const identity_overview = t`InvenTree can be integrated with external Identity Providers and act as one.`;
  const identity_inbound = t`External Identities can be pushed to InvenTree via Single Sign-On (SSO) and SCIM.`;
  const identity_outbound = t`InvenTree can act as an Identity Provider for external applications via the built-in oAuth2 provider.`;

  return (
    <>
      {identity_overview}
      <SimpleGrid cols={2} spacing='md' mt='md' mb='md'>
        <div>{identity_inbound}</div>
        <div>{identity_outbound}</div>
      </SimpleGrid>

      <Accordion
        variant='separated'
        defaultValue={['scim']}
        chevronPosition='left'
        multiple
      >
        <Accordion.Item value='scim'>
          <Accordion.Control>
            {headerSection(t`SCIM Provisioning`)}
          </Accordion.Control>
          <Accordion.Panel>
            <ScimManagementPanel />
          </Accordion.Panel>
        </Accordion.Item>
        <Accordion.Item value='sso'>
          <Accordion.Control>
            {headerSection(t`Single Sign-On (SSO)`)}
          </Accordion.Control>
          <Accordion.Panel>
            <SSOManagementPanel />
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>
    </>
  );
}
