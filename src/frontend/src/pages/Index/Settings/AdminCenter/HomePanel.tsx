import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import { Alert, Button, SimpleGrid, Stack, Title } from '@mantine/core';
import { IconBrandGithub } from '@tabler/icons-react';
import { type JSX, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useShallow } from 'zustand/react/shallow';
import { ServerAlert, getAlerts } from '../../../../components/nav/Alerts';
import { QuickAction } from '../../../../components/settings/QuickAction';
import { useServerApiState } from '../../../../states/ServerApiState';
import { useGlobalSettingsState } from '../../../../states/SettingsStates';

export default function HomePanel(): JSX.Element {
  const [dismissed, setDismissed] = useState<boolean>(false);
  const [server] = useServerApiState(useShallow((state) => [state.server]));
  const globalSettings = useGlobalSettingsState();

  const alerts = useMemo(
    () => getAlerts(server, globalSettings),
    [server, globalSettings]
  );

  return (
    <Stack gap='xs'>
      {dismissed ? null : (
        <Alert
          color='blue'
          title={t`This is new!`}
          withCloseButton
          onClose={() => setDismissed(true)}
        >
          <Trans>
            The home menu (and the whole Admin center) is a new feature starting
            with the new UI and was previously (before 1.0) not available. It
            provides a centralized location for all administration functionality
            and is meant to replace the (django) backend admin interface.
          </Trans>
          <br />
          <Trans>
            Please raise issues (after checking the tracker) for any missing
            admin functionality. The backend admin interface should only be used
            very carefully and seldome.
          </Trans>
          <br />
          <Button
            color='green'
            component={Link}
            size='compact-md'
            to={'https://github.com/inventree/InvenTree/issues/new'}
            target='_blank'
          >
            <IconBrandGithub /> <Trans>Open an issue</Trans>
          </Button>
        </Alert>
      )}
      <QuickAction ml='' />
      <Title order={5}>
        <Trans>System status</Trans>
      </Title>
      {alerts.length > 0 ? (
        <SimpleGrid cols={2} spacing='sm'>
          {alerts.map((alert) => (
            <ServerAlert alert={alert} />
          ))}
        </SimpleGrid>
      ) : (
        <Alert color='green'>{t`No system alerts`}</Alert>
      )}
      <Title order={5}>
        <Trans>Security recommodations</Trans>
      </Title>
      TBD
    </Stack>
  );
}
