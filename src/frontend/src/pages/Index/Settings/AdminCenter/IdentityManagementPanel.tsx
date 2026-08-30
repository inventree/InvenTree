import { CopyButton } from '@lib/components/CopyButton';
import { StylishText } from '@lib/components/StylishText';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { navigateToLink } from '@lib/functions/Navigation';
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
  IconShieldLock,
  IconShieldOff
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, queryClient } from '../../../../App';
import { GlobalSettingList } from '../../../../components/settings/SettingList';
import { showApiErrorMessage } from '../../../../functions/notifications';

function ScimManagementPanel() {
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

  const scimTableData = useMemo(
    () => [
      [
        <Trans>Status</Trans>,
        data?.enabled ? (
          <Badge color='green'>
            <Trans>Enabled</Trans>
          </Badge>
        ) : (
          <Badge color='gray'>
            <Trans>Disabled</Trans>
          </Badge>
        )
      ],
      [
        <Trans>Base URL</Trans>,
        <Group gap='xs' wrap='nowrap'>
          <Code>{data?.base_url}</Code>
          <CopyButton value={data?.base_url} />
        </Group>
      ],
      [<Trans>Secret Generated</Trans>, data?.secret_generated ?? '-'],
      [<Trans>Last Used</Trans>, data?.last_used ?? '-']
    ],
    [data?.enabled, data?.base_url, data?.secret_generated, data?.last_used]
  );

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
          Groups.
        </Trans>
      </Alert>

      <Table data={{ body: scimTableData }} />

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
  const authenticationSettingsPath = '/settings/system/authentication';
  const navigate = useNavigate();
  return (
    <Stack gap='md'>
      <Alert icon={<IconShieldLock />} color='blue'>
        Actual mgmt TBD
      </Alert>
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
              navigateToLink(authenticationSettingsPath, navigate, event)
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
        <Accordion.Item value='oauth2'>
          <Accordion.Control>
            {headerSection(t`oAuth2 Provider`, true)}
          </Accordion.Control>
          <Accordion.Panel>TBD</Accordion.Panel>
        </Accordion.Item>
      </Accordion>
    </>
  );
}
