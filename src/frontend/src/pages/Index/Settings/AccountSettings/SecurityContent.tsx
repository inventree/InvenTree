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
  Text,
  TextInput,
  Title,
  Tooltip
} from '@mantine/core';
import { IconAlertCircle, IconAt } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

import { api, queryClient } from '../../../../App';
import { PlaceholderPill } from '../../../../components/items/Placeholder';
import { ApiPaths } from '../../../../enums/ApiEndpoints';
import { apiUrl } from '../../../../states/ApiState';
import { useUserState } from '../../../../states/UserState';

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
    </Stack>
  );
}

function EmailContent({}: {}) {
  const [value, setValue] = useState<string>('');
  const [newEmailValue, setNewEmailValue] = useState('');
  const [user] = useUserState((state) => [state.user]);
  const { isLoading, data, refetch } = useQuery({
    queryKey: ['emails'],
    queryFn: () => api.get(apiUrl(ApiPaths.user_emails)).then((res) => res.data)
  });

  function runServerAction(url: ApiPaths) {
    api
      .post(apiUrl(url, undefined, { id: value }), {})
      .then(() => {
        refetch();
      })
      .catch((res) => console.log(res.data));
  }

  function addEmail() {
    api
      .post(apiUrl(ApiPaths.user_emails), {
        email: newEmailValue,
        user: user?.pk
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
      </Grid.Col>
      <Grid.Col span={6}>
        <Stack>
          <Text>
            <Trans>Add Email Address</Trans>
          </Text>
          <TextInput
            label={t`E-Mail`}
            placeholder={t`E-Mail address`}
            icon={<IconAt />}
            value={newEmailValue}
            onChange={(event) => setNewEmailValue(event.currentTarget.value)}
          />
        </Stack>
      </Grid.Col>
      <Grid.Col span={6}>
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
      </Grid.Col>
      <Grid.Col span={6}>
        <Button onClick={addEmail}>
          <Trans>Add Email</Trans>
        </Button>
      </Grid.Col>
    </Grid>
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
      .post(apiUrl(ApiPaths.user_sso_remove, undefined, { id: value }))
      .then(() => {
        queryClient.removeQueries({
          queryKey: ['sso-list']
        });
      })
      .catch((res) => console.log(res.data));
  }

  /* renderer */
  if (isLoading) return <Loader />;

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
    <Grid>
      <Grid.Col span={6}>
        {data.length == 0 ? (
          <Alert
            icon={<IconAlertCircle size="1rem" />}
            title={t`Not configured`}
            color="yellow"
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
              name="sso_accounts"
              label={t`You can sign in to your account using any of the following third party accounts`}
            >
              <Stack mt="xs">
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
              <Stack spacing="xs">
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

function MfaContent({}: {}) {
  return (
    <>
      MFA Details
      <PlaceholderPill />
    </>
  );
}
