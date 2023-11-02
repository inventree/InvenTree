import { Trans, t } from '@lingui/macro';
import {
  Alert,
  Badge,
  Button,
  Group,
  Loader,
  Radio,
  Stack,
  Text,
  Title,
  Tooltip
} from '@mantine/core';
import { IconAlertCircle } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

import { api, queryClient } from '../../../../App';
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
  const [value, setValue] = useState<string>('');
  const { isLoading, data, refetch } = useQuery({
    queryKey: ['emails'],
    queryFn: () => api.get(apiUrl(ApiPaths.user_emails)).then((res) => res.data)
  });

  function runServerAction(url: ApiPaths) {
    api
      .post(apiUrl(url).replace('$id', value), {})
      .then(() => {
        refetch();
      })
      .catch((res) => console.log(res.data));
  }

  if (isLoading) return <Loader />;

  return (
    <Group>
      <Stack>
        <Radio.Group
          value={value}
          onChange={setValue}
          name="email_accounts"
          label={t`The following email addresses are associated with your account:`}
        >
          <Stack mt="xs">
            {data.map((link: any) => (
              <Radio
                key={link.id}
                value={String(link.id)}
                label={
                  <Group position="apart">
                    {link.email}
                    {link.primary && (
                      <Badge color="blue">
                        <Trans>Primary</Trans>
                      </Badge>
                    )}
                    {link.verified ? (
                      <Badge color="green">
                        <Trans>Verified</Trans>
                      </Badge>
                    ) : (
                      <Badge color="yellow">
                        <Trans>Unverified</Trans>
                      </Badge>
                    )}
                  </Group>
                }
              />
            ))}
          </Stack>
        </Radio.Group>
        <Group>
          <Button onClick={() => runServerAction(ApiPaths.user_email_primary)}>
            <Trans>Make Primary</Trans>
          </Button>
          <Button onClick={() => runServerAction(ApiPaths.user_email_verify)}>
            <Trans>Re-send Verification</Trans>
          </Button>
          <Button onClick={() => runServerAction(ApiPaths.user_email_remove)}>
            <Trans>Remove</Trans>
          </Button>
        </Group>
      </Stack>
      <Stack>
        <Text>
          <Trans>Add Email Address</Trans>
        </Text>
      </Stack>
    </Group>
  );
}

function SsoContent({ dataProvider }: { dataProvider: any | undefined }) {
  const [value, setValue] = useState<string>('');
  const [currentProviders, setcurrentProviders] = useState<[]>();
  const { isLoading, data } = useQuery({
    queryKey: ['sso-list'],
    queryFn: () => api.get(apiUrl(ApiPaths.user_sso)).then((res) => res.data)
  });

  useEffect(() => {
    if (dataProvider === undefined) return;
    if (data === undefined) return;

    const configuredProviders = data.map((item: any) => {
      return item.provider;
    });
    function isAlreadyInUse(value: any) {
      return !configuredProviders.includes(value.id);
    }

    // remove providers that are used currently
    let newData = dataProvider.providers;
    newData = newData.filter(isAlreadyInUse);
    setcurrentProviders(newData);
  }, [dataProvider, data]);

  function removeProvider() {
    api
      .post(apiUrl(ApiPaths.user_sso_remove).replace('$id', value))
      .then(() => {
        queryClient.removeQueries({
          queryKey: ['sso-list']
        });
      })
      .catch((res) => console.log(res.data));
  }

  /* renderer */
  function ProviderButton({ provider }: { provider: any }) {
    const button = (
      <Button
        key={provider.id}
        component="a"
        href={provider.connect}
        variant="outline"
        disabled={!provider.configured}
      >
        <Group position="apart">
          {provider.display_name}
          {provider.configured == false && <IconAlertCircle />}
        </Group>
      </Button>
    );

    if (provider.configured) return button;
    return (
      <Tooltip label={t`Provider has not been configured`}>{button}</Tooltip>
    );
  }

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
              <Stack>
                <Radio.Group
                  value={value}
                  onChange={setValue}
                  name="sso_accounts"
                  label={t`You can sign in to your account using any of the following third party accounts`}
                >
                  <Group mt="xs">
                    {data.map((link: any) => (
                      <Radio
                        key={link.id}
                        value={String(link.id)}
                        label={link.provider}
                      />
                    ))}
                  </Group>
                </Radio.Group>
                <Button onClick={removeProvider}>
                  <Trans>Remove</Trans>
                </Button>
              </Stack>
            )}
            <Stack>
              <Text>Add SSO Account</Text>
              <Text>
                {currentProviders === undefined ? (
                  <Trans>Loading</Trans>
                ) : (
                  <Stack spacing="xs">
                    {currentProviders.map((provider: any) => (
                      <ProviderButton key={provider.id} provider={provider} />
                    ))}
                  </Stack>
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
