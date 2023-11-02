import { Trans, t } from '@lingui/macro';
import {
  Alert,
  Button,
  Group,
  Loader,
  Stack,
  Text,
  Title
} from '@mantine/core';
import { IconAlertCircle } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

import { api } from '../../../../App';
import { PlaceholderPill } from '../../../../components/items/Placeholder';
import { ApiPaths, apiUrl } from '../../../../states/ApiState';

export function SecurityContent() {
  const [isSsoEnabled, setIsSsoEnabled] = useState<boolean>(false);
  const [isMfaEnabled, setIsMfaEnabled] = useState<boolean>(false);

  const { isLoading: isLoadingProvider, data: dataProvider } = useQuery({
    queryKey: ['sso-providers'],
    queryFn: () =>
      api.get(apiUrl(ApiPaths.sso_providers)).then((res) => res.data)
  });

  // evaluate if security options are enabled
  useEffect(() => {
    if (dataProvider === undefined) return;

    // check if SSO is enabled on the server
    setIsSsoEnabled(dataProvider.sso_enabled || false);
    // check if MFa is enabled
    setIsMfaEnabled(dataProvider.mfa_required || false);
  }, [dataProvider]);

  return (
    <Stack>
      <Title order={5}>
        <Trans>Email</Trans>
      </Title>
      <EmailContent />
      <Title order={5}>
        <Trans>Single Sign On Accounts</Trans>
      </Title>
      {isSsoEnabled ? (
        <SsoContent dataProvider={dataProvider} />
      ) : (
        <Alert
          icon={<IconAlertCircle size="1rem" />}
          title={t`Not enabled`}
          color="yellow"
        >
          <Trans>Single Sign On is not enabled for this server </Trans>
        </Alert>
      )}
      <Title order={5}>
        <Trans>Multifactor</Trans>
      </Title>
      {isLoadingProvider ? (
        <Loader />
      ) : (
        <>
          {isMfaEnabled ? (
            <MfaContent />
          ) : (
            <Alert
              icon={<IconAlertCircle size="1rem" />}
              title={t`Not enabled`}
              color="yellow"
            >
              <Trans>
                Multifactor authentication is not configured for your account{' '}
              </Trans>
            </Alert>
          )}
        </>
      )}
      <Title order={5}>
        <Trans>Active Sessions</Trans>
      </Title>
      <ActiveSessionContent />
    </Stack>
  );
}

function EmailContent({}: {}) {
  return (
    <>
      Email Details
      <PlaceholderPill />
    </>
  );
}

function SsoContent({ dataProvider }: { dataProvider: any | undefined }) {
  const { isLoading, data } = useQuery({
    queryKey: ['sso-list'],
    queryFn: () => api.get(apiUrl(ApiPaths.user_sso)).then((res) => res.data)
  });

  return (
    <>
      {isLoading ? (
        <Loader />
      ) : (
        <>
          <Group>
            {data.length == 0 ? (
              <Alert
                icon={<IconAlertCircle size="1rem" />}
                title={t`Not configured`}
                color="yellow"
              >
                <Trans>
                  There are no social network accounts connected to this
                  account.{' '}
                </Trans>
              </Alert>
            ) : (
              <Text>
                Currently registered SSO providers
                <br />
                {JSON.stringify(data)}
              </Text>
            )}
            <Stack>
              <Text>Possible SSO providers</Text>
              <Text>
                {dataProvider === undefined ? (
                  <Trans>Loading</Trans>
                ) : (
                  <>
                    {dataProvider.providers.map((provider: any) => {
                      return (
                        <Button
                          key={provider.id}
                          component="a"
                          href={provider.connect}
                          variant="outline"
                        >
                          {provider.display_name}
                        </Button>
                      );
                    })}
                  </>
                )}
              </Text>
            </Stack>
          </Group>
        </>
      )}
    </>
  );
}

function MfaContent({}: {}) {
  return (
    <>
      MFA Details
      <PlaceholderPill />
    </>
  );
}

function ActiveSessionContent({}: {}) {
  return (
    <>
      Active Session Details
      <PlaceholderPill />
    </>
  );
}
